import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, OnDestroy, OnInit } from '@angular/core';
import { FormArray, FormBuilder, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { HttpClient, HttpHeaders, HttpResponse } from '@angular/common/http';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { Subject, Subscription, debounceTime, finalize } from 'rxjs';

// ─────────────────────────────────────────────────────────────────────────────
// Temas: colores de encabezado sincronizados con backend/cv_design_theme.py
// ─────────────────────────────────────────────────────────────────────────────
const THEME_COUNT = 5;
const THEME_HEADER_COLORS = ['#ededed', '#e5edf7', '#f2ede0', '#e8f2e8', '#f2edf7'];
const THEME_NAMES         = ['Clásico', 'Ejecutivo', 'Moderno', 'Corporativo', 'Elegante'];

// ─────────────────────────────────────────────────────────────────────────────
// Fuentes disponibles (deben coincidir con las claves de font_registry.py).
// ─────────────────────────────────────────────────────────────────────────────
interface FontOption { key: string; label: string; }
const FONT_OPTIONS: FontOption[] = [
  { key: 'helvetica',  label: 'Sans · Helvetica'       },
  { key: 'arial',      label: 'Profesional · Arial'    },
  { key: 'calibri',    label: 'Moderna · Calibri'      },
  { key: 'verdana',    label: 'Legible · Verdana'      },
  { key: 'trebuchet',  label: 'Compacta · Trebuchet MS'},
  { key: 'times',      label: 'Serif · Times Roman'    },
  { key: 'georgia',    label: 'Elegante · Georgia'     },
  { key: 'garamond',   label: 'Clásica · Garamond'     },
  { key: 'courier',    label: 'Técnica · Courier'      },
];

// ─────────────────────────────────────────────────────────────────────────────
// Pesos para el indicador de completitud
// ─────────────────────────────────────────────────────────────────────────────
interface CompletionCheck { id: string; label: string; weight: number; }
const COMPLETION_CHECKS: CompletionCheck[] = [
  { id: 'nombre',           label: 'Agrega tu nombre completo',                  weight: 10 },
  { id: 'profesion',        label: 'Indica tu profesión',                         weight: 10 },
  { id: 'email',            label: 'Incluye tu correo electrónico',               weight: 8  },
  { id: 'telefono',         label: 'Agrega un número de teléfono',                weight: 6  },
  { id: 'ciudad',           label: 'Indica tu ciudad',                            weight: 4  },
  { id: 'linkedin',         label: 'Agrega tu perfil de LinkedIn',                weight: 5  },
  { id: 'foto',             label: 'Una foto profesional atrae más atención',     weight: 8  },
  { id: 'descripcion',      label: 'Escribe una breve descripción personal',      weight: 7  },
  { id: 'experiencia',      label: 'Completa al menos una experiencia laboral',   weight: 15 },
  { id: 'educacion',        label: 'Completa tu formación académica',             weight: 12 },
  { id: 'soft_skills',      label: 'Menciona tus habilidades blandas',            weight: 7  },
  { id: 'disponibilidad',   label: 'Indica tu disponibilidad laboral',            weight: 5  },
  { id: 'hobbies',          label: 'Los intereses personales humanizan tu CV',    weight: 2  },
  { id: 'certificaciones',  label: 'Añade certificaciones para destacar',         weight: 1  },
];

@Component({
  selector: 'app-root',
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './app.html'
})
export class App implements OnInit, OnDestroy {
  private readonly apiBaseUrl = 'http://localhost:8000';
  private readonly STORAGE_KEY = 'cvgen_autosave_v1';

  // ── Tema ──────────────────────────────────────────────────────────────────
  isDarkTheme = true;

  toggleTheme(): void {
    this.isDarkTheme = !this.isDarkTheme;
    this._applyTheme();
  }

  private _applyTheme(): void {
    document.body.classList.toggle('light-theme', !this.isDarkTheme);
    localStorage.setItem('cvgen_theme', this.isDarkTheme ? 'dark' : 'light');
  }

  // ── Estado UI ─────────────────────────────────────────────────────────────
  loading = false;
  errorMessage: string | null = null;
  pdfUrl: string | null = null;
  previewSrcSafe: SafeResourceUrl | null = null;
  previewLoading  = false;
  photoName: string | null = null;
  showPreferences = false;

  // ── Auto-guardado ─────────────────────────────────────────────────────────
  lastSaved: Date | null = null;
  hasSavedData = false;

  get lastSavedText(): string {
    if (!this.lastSaved) return '';
    const secs = Math.floor((Date.now() - this.lastSaved.getTime()) / 1000);
    if (secs < 5)  return 'Guardado';
    if (secs < 60) return `Guardado hace ${secs}s`;
    return `Guardado hace ${Math.floor(secs / 60)} min`;
  }

  // ── Completitud ───────────────────────────────────────────────────────────
  get completionScore(): number {
    const v = this.form?.value;
    if (!v) return 0;
    let total = 0;
    let filled = 0;
    for (const chk of COMPLETION_CHECKS) {
      total += chk.weight;
      if (this._isCheckFilled(chk.id, v)) filled += chk.weight;
    }
    return Math.round((filled / total) * 100);
  }

  get completionTip(): string {
    const v = this.form?.value;
    if (!v) return '';
    for (const chk of COMPLETION_CHECKS) {
      if (!this._isCheckFilled(chk.id, v)) return chk.label;
    }
    return '¡CV completo! Listo para descargar.';
  }

  private _isCheckFilled(id: string, v: any): boolean {
    switch (id) {
      case 'nombre':          return !!v.nombre?.trim();
      case 'profesion':       return !!v.profesion?.trim();
      case 'email':           return !!v.email?.trim();
      case 'telefono':        return !!v.telefono?.trim();
      case 'ciudad':          return !!v.ciudad?.trim();
      case 'linkedin':        return !!v.linkedin?.trim();
      case 'foto':            return !!v.foto_base64;
      case 'descripcion':     return !!v.breve_descripcion?.trim();
      case 'experiencia':     return (v.experiencia_laboral || []).some((e: any) => e.empresa?.trim());
      case 'educacion':       return (v.educacion || []).some((e: any) => e.titulo?.trim());
      case 'soft_skills':     return !!v.soft_skills_text?.trim();
      case 'disponibilidad':  return !!v.disponibilidad_laboral?.trim();
      case 'hobbies':         return !!v.hobbies_text?.trim();
      case 'certificaciones': return !!v.certificaciones_text?.trim();
      default: return false;
    }
  }

  // ── Diseño ────────────────────────────────────────────────────────────────
  designVariant = 0;
  readonly fontOptions = FONT_OPTIONS;

  get currentThemeName(): string { return THEME_NAMES[this.designVariant] ?? 'Clásico'; }

  // ── Internos ──────────────────────────────────────────────────────────────
  private previewSeq   = 0;
  private previewSub: Subscription | null = null;
  private saveSub: Subscription | null = null;
  private previewTimer: number | null = null;

  /** Solo para typing en inputs de texto (debounce 2 s). */
  private readonly textChanges$ = new Subject<void>();

  form!: FormGroup;
  prefsForm!: FormGroup;

  constructor(
    private fb: FormBuilder,
    private http: HttpClient,
    private sanitizer: DomSanitizer,
    private cdr: ChangeDetectorRef,
  ) {}

  // ── Ciclo de vida ─────────────────────────────────────────────────────────

  ngOnInit(): void {
    this.form = this.fb.group({
      nombre:               [''],
      profesion:            [''],
      breve_descripcion:    [''],
      foto_base64:          [null],

      experiencia_laboral:  this.fb.array([this.buildExperienceGroup()]),
      soft_skills_text:     [''],

      educacion:            this.fb.array([this.buildEducationGroup()]),
      hobbies_text:         [''],
      certificaciones_text: [''],

      email:                [''],
      telefono:             [''],
      linkedin:             [''],
      website:              [''],
      ciudad:               [''],

      disponibilidad_laboral: [''],
    });

    this.prefsForm = this.fb.group({
      font_family:     [FONT_OPTIONS[0].key],
      foto_position:   ['top-right'],
      accent_color:    ['#111111'],
      header_bg_color: [THEME_HEADER_COLORS[0]],
    });

    // Cargar tema
    if (localStorage.getItem('cvgen_theme') === 'light') {
      this.isDarkTheme = false;
    }
    this._applyTheme();

    // Cargar datos guardados antes de suscribirse
    this.loadFromStorage();

    // Vista previa con debounce
    this.previewSub = this.form.valueChanges
      .pipe(debounceTime(500))
      .subscribe(() => this.updatePreview());

    // Preferencias: misma lógica que el form principal
    this.prefsForm.valueChanges
      .pipe(debounceTime(500))
      .subscribe(() => this.updatePreview());

    // Auto-guardado independiente
    this.saveSub = this.form.valueChanges
      .pipe(debounceTime(800))
      .subscribe(() => this.saveToStorage());

    // Primera renderización
    this.updatePreview();
  }

  ngOnDestroy(): void {
    if (this.previewSub) this.previewSub.unsubscribe();
    if (this.saveSub)    this.saveSub.unsubscribe();
    if (this.previewTimer) window.clearTimeout(this.previewTimer);
    if (this.pdfUrl) URL.revokeObjectURL(this.pdfUrl);
  }

  // ── Getters FormArray ─────────────────────────────────────────────────────

  get experiencias(): FormArray { return this.form.get('experiencia_laboral') as FormArray; }
  get educaciones():  FormArray { return this.form.get('educacion') as FormArray; }

  // ── Constructores de grupos ───────────────────────────────────────────────

  private buildExperienceGroup(): FormGroup {
    return this.fb.group({
      empresa:     [''],
      puesto:      [''],
      anio_inicio: [''],
      anio_fin:    [''],
      descripcion: [''],
    });
  }

  private buildEducationGroup(): FormGroup {
    return this.fb.group({
      titulo:      [''],
      institucion: [''],
      anio_inicio: [''],
      anio_fin:    [''],
    });
  }

  // ── Manejo de arrays ──────────────────────────────────────────────────────

  addExperience():               void { this.experiencias.push(this.buildExperienceGroup()); this.updatePreview(); }
  removeExperience(i: number):   void { this.experiencias.removeAt(i); this.updatePreview(); }
  addEducation():                void { this.educaciones.push(this.buildEducationGroup()); this.updatePreview(); }
  removeEducation(i: number):    void { this.educaciones.removeAt(i); this.updatePreview(); }

  // ── Triggers de preview ───────────────────────────────────────────────────

  onFormInput(event: Event): void {
    const el = event.target as HTMLInputElement;
    if (
      el.tagName === 'TEXTAREA' ||
      (el.tagName === 'INPUT' && el.type !== 'color' && el.type !== 'file')
    ) {
      this.textChanges$.next();
    }
  }

  // ── Diseño ────────────────────────────────────────────────────────────────

  shuffleDesign(): void {
    this.designVariant = (this.designVariant + 1) % THEME_COUNT;
    this.prefsForm.patchValue(
      { header_bg_color: THEME_HEADER_COLORS[this.designVariant] },
      { emitEvent: false },
    );
    this.saveToStorage();
    this.updatePreview();
  }

  // ── Foto ──────────────────────────────────────────────────────────────────

  onPhotoSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file  = input.files?.[0];
    if (!file) return;
    this.photoName = file.name;
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result || '');
      const base64 = result.includes('base64,') ? result.split('base64,')[1] : null;
      window.setTimeout(() => {
        this.form.patchValue({ foto_base64: base64 }, { emitEvent: false });
        this.saveToStorage();
        this.updatePreview();
      }, 0);
    };
    reader.readAsDataURL(file);
  }

  // ── Auto-guardado ─────────────────────────────────────────────────────────

  private saveToStorage(): void {
    try {
      const data = {
        form:          this.form.value,
        prefs:         this.prefsForm.value,
        designVariant: this.designVariant,
        photoName:     this.photoName,
        savedAt:       new Date().toISOString(),
      };
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(data));
      this.lastSaved   = new Date();
      this.hasSavedData = true;
    } catch {
      // localStorage no disponible (modo privado sin cuota, etc.)
    }
  }

  private loadFromStorage(): void {
    try {
      const raw = localStorage.getItem(this.STORAGE_KEY);
      if (!raw) return;
      const data = JSON.parse(raw);

      // Restaurar arrays de experiencia
      if (data.form?.experiencia_laboral?.length) {
        while (this.experiencias.length > 0) this.experiencias.removeAt(0);
        for (const exp of data.form.experiencia_laboral) {
          const g = this.buildExperienceGroup();
          g.patchValue(exp);
          this.experiencias.push(g);
        }
      }

      // Restaurar arrays de educación
      if (data.form?.educacion?.length) {
        while (this.educaciones.length > 0) this.educaciones.removeAt(0);
        for (const edu of data.form.educacion) {
          const g = this.buildEducationGroup();
          g.patchValue(edu);
          this.educaciones.push(g);
        }
      }

      // Restaurar campos simples (excluye los arrays ya procesados)
      if (data.form) {
        const { experiencia_laboral, educacion, ...rest } = data.form;
        this.form.patchValue(rest, { emitEvent: false });
      }

      if (data.prefs) {
        this.prefsForm.patchValue(data.prefs, { emitEvent: false });
      }

      if (data.designVariant !== undefined) {
        this.designVariant = data.designVariant;
      }

      if (data.photoName) {
        this.photoName = data.photoName;
      }

      this.lastSaved    = data.savedAt ? new Date(data.savedAt) : null;
      this.hasSavedData = true;
    } catch {
      // Datos corruptos: ignorar
    }
  }

  clearAll(): void {
    if (!confirm('¿Borrar todos los datos del formulario? Esta acción no se puede deshacer.')) return;

    localStorage.removeItem(this.STORAGE_KEY);

    // Resetear arrays
    while (this.experiencias.length > 0) this.experiencias.removeAt(0);
    this.experiencias.push(this.buildExperienceGroup());
    while (this.educaciones.length > 0) this.educaciones.removeAt(0);
    this.educaciones.push(this.buildEducationGroup());

    this.form.reset({ output_format: 'pdf' }, { emitEvent: false });
    this.prefsForm.patchValue({
      font_family:     FONT_OPTIONS[0].key,
      foto_position:   'top-right',
      accent_color:    '#111111',
      header_bg_color: THEME_HEADER_COLORS[0],
    }, { emitEvent: false });

    this.designVariant = 0;
    this.photoName     = null;
    this.lastSaved     = null;
    this.hasSavedData  = false;

    this.updatePreview();
  }

  // ── Payload ───────────────────────────────────────────────────────────────

  private csvToList(value: string): string[] {
    return (value || '').split(',').map(x => x.trim()).filter(Boolean);
  }

  private buildRequestPayload(v: any, outputFormat: 'pdf' | 'docx'): any {
    const p = this.prefsForm.value;
    const s = (val: any): string => val ?? '';   // null / undefined → ''
    return {
      cv: {
        nombre:               s(v.nombre),
        profesion:            s(v.profesion),
        breve_descripcion:    v.breve_descripcion ? String(v.breve_descripcion) : null,
        foto_base64:          v.foto_base64 ?? null,
        experiencia_laboral:  (v.experiencia_laboral || []).map((e: any) => ({
          empresa:     s(e.empresa),
          puesto:      s(e.puesto),
          anio_inicio: s(e.anio_inicio),
          anio_fin:    s(e.anio_fin),
          descripcion: s(e.descripcion),
        })),
        soft_skills:          this.csvToList(v.soft_skills_text),
        educacion:            (v.educacion || []).map((ed: any) => ({
          institucion: s(ed.institucion),
          titulo:      s(ed.titulo),
          anio_inicio: s(ed.anio_inicio),
          anio_fin:    s(ed.anio_fin),
        })),
        hobbies:              v.hobbies_text ? this.csvToList(v.hobbies_text) : null,
        certificaciones:      v.certificaciones_text
          ? this.csvToList(v.certificaciones_text).map((nombre: string) => ({ nombre }))
          : null,
        contacto: {
          email:    s(v.email),
          telefono: s(v.telefono),
          linkedin: s(v.linkedin),
          website:  s(v.website),
          ciudad:   s(v.ciudad),
        },
        disponibilidad_laboral: s(v.disponibilidad_laboral),
      },
      output_format: outputFormat,
      font_color:    p.accent_color,
      design_preferences: {
        design_variant:  this.designVariant,
        foto_position:   p.foto_position,
        font_family:     p.font_family,
        header_bg_color: p.header_bg_color || null,
      },
    };
  }

  // ── Valores con placeholders ──────────────────────────────────────────────

  private _safeValues(): any {
    const v = this.form.value;
    const t = (val: any, fallback: string) => val?.trim() ? String(val) : fallback;
    return {
      ...v,
      nombre:                 t(v.nombre,                 'Tu nombre'),
      profesion:              t(v.profesion,              'Profesión'),
      disponibilidad_laboral: t(v.disponibilidad_laboral, 'A convenir'),
      email:                  t(v.email,                  'correo@ejemplo.com'),
      experiencia_laboral: (v.experiencia_laboral || []).map((e: any) => ({
        empresa:     t(e.empresa,     'Empresa'),
        puesto:      t(e.puesto,      'Puesto'),
        anio_inicio: t(e.anio_inicio, '2022'),
        anio_fin:    t(e.anio_fin,    '2024'),
        descripcion: e.descripcion ?? '',
      })),
      educacion: (v.educacion || []).map((ed: any) => ({
        institucion: t(ed.institucion, 'Institución'),
        titulo:      t(ed.titulo,      'Título'),
        anio_inicio: t(ed.anio_inicio, '2020'),
        anio_fin:    t(ed.anio_fin,    '2024'),
      })),
    };
  }

  // ── Vista previa ──────────────────────────────────────────────────────────

  updatePreview(): void {
    const safe  = this._safeValues();
    const seq   = ++this.previewSeq;
    const payload = this.buildRequestPayload(safe, 'pdf');

    if (this.previewTimer) window.clearTimeout(this.previewTimer);
    this.previewTimer = window.setTimeout(() => {
      if (seq !== this.previewSeq) return;
      this.previewLoading = true;

      this.http
        .post(`${this.apiBaseUrl}/api/cv/generate`, payload, {
          responseType: 'blob',
          observe: 'response',
          headers: new HttpHeaders({ 'x-cv-preview': '1' }),
        })
        .subscribe({
          next: (res: HttpResponse<Blob>) => {
            if (seq !== this.previewSeq) return;

            this.previewLoading = false;

            const blob = res.body;
            if (!blob) return;

            const objectUrl = URL.createObjectURL(blob);
            const oldUrl = this.pdfUrl;

            this.pdfUrl = objectUrl;
            this.previewSrcSafe = this.sanitizer.bypassSecurityTrustResourceUrl(objectUrl + '#page=1');

            this.cdr.detectChanges();

            if (oldUrl) {
              setTimeout(() => URL.revokeObjectURL(oldUrl), 10000);
            }
          },
          error: (err) => {
            if (seq !== this.previewSeq) return;
            this.previewLoading = false;
            console.error(err);
          },
        });
    }, 0);
  }

  // ── Generación final ──────────────────────────────────────────────────────

  private parseFilename(cd: string | null): string | null {
    if (!cd) return null;
    return /filename=\"?([^";]+)\"?/i.exec(cd)?.[1] ?? null;
  }

  onGenerate(): void {
    this.errorMessage = null;
    this.loading = true;
    const safe    = this._safeValues();
    const payload = this.buildRequestPayload(safe, 'pdf');

    this.http
      .post(`${this.apiBaseUrl}/api/cv/generate`, payload, { responseType: 'blob', observe: 'response' })
      .pipe(finalize(() => { this.loading = false; this.cdr.detectChanges(); }))
      .subscribe({
        next: (res: HttpResponse<Blob>) => {
          const blob = res.body;
          if (!blob) { this.errorMessage = 'No se generó ningún archivo.'; return; }
          const filename  = this.parseFilename(res.headers.get('content-disposition')) || 'cv.pdf';
          const objectUrl = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = objectUrl; a.download = filename; a.click();
          if (this.pdfUrl) URL.revokeObjectURL(this.pdfUrl);
          this.pdfUrl = objectUrl;
        },
        error: (err) => {
          this.errorMessage = 'Error generando el CV. Verifica el backend.';
          console.error(err);
        },
      });
  }
}
