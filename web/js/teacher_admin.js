/*
 * Administration des enseignants — Service déclaré & disposition.
 * Complète web/js/app.js : ajoute la gestion du service (plein/demi/custom)
 * et l'affichage du bilan HETD dans l'onglet "Enseignants & Demi-Journées".
 *
 * Les variables globales (dataset, constraints, currentSchedule, DAYS, createDiv) sont
 * définies dans app.js ; ce fichier est chargé APRÈS app.js.
 */

// État local : services déclarés chargés depuis /api/v1/admin/teacher-services
let teacherServices = {};

const SERVICE_PLAIN_HETD = 384;   // service plein (temps complet)
const SERVICE_DEMI_HETD = 192;    // demi-service
const MODE_LABELS = { PLAIN: 'Service plein (384 h)', DEMI: 'Demi-service (192 h)', CUSTOM: 'Service custom (heures réelles)' };


// Charge les services déclarés depuis le backend (constraints.json).
async function loadTeacherServices() {
    try {
        const r = await fetch('/api/v1/admin/teacher-services');
        teacherServices = (await r.json()) || {};
    } catch (e) {
        teacherServices = {};
    }
    return teacherServices;
}

// Retourne le service effectif d'un enseignant (mode + HETD).
function getTeacherService(teacherName) {
    const svc = teacherServices[teacherName];
    if (svc) return { mode: svc.mode || 'CUSTOM', hetd: Number(svc.hetd) || 0 };
    const t = (dataset.teachers || []).find(x => x.name === teacherName);
    const base = t ? Number(t.service_statutaire_hetd) || 0 : 0;
    let mode = 'CUSTOM';
    if (base >= SERVICE_PLAIN_HETD) mode = 'PLAIN';
    else if (base === SERVICE_DEMI_HETD) mode = 'DEMI';
    return { mode, hetd: base };
}

// Calcule le total HETD planifié d'un enseignant (toutes semaines).
// Utilise normalizeTeacherKey (app.js) pour un matching insensible à l'ordre
// des noms (ex: "Steeve Pytel" ≈ "Pytel Steeve") et aux accents/bruit "Mémo:"/"Salles:".
function computeTeacherHETD(teacherName) {
    const norm = typeof normalizeTeacherKey === 'function' ? normalizeTeacherKey : (s => String(s || '').toLowerCase());
    const want = norm(teacherName).split(' ').filter(Boolean);
    const events = (currentSchedule || []).filter(e => {
        const evKey = norm(e.teacher_name);
        return want.length && want.every(w => evKey.includes(w));
    });
    let hetd = 0, autres = 0, autresNb = 0;
    events.forEach(e => {
        const dur = e.duration_hours || 1.5;
        if (e.is_other || e.event_type === 'AUTRE') {
            autres += dur;
            autresNb += 1;
            return;
        }
        if (e.event_type === 'CM') hetd += dur * 1.5;
        else if (e.event_type === 'TP') hetd += dur * 0.75;
        else hetd += dur * 1.0;
    });
    return { hetdCours: Math.round(hetd * 10) / 10, heuresAutres: Math.round(autres * 10) / 10, nbAutres: autresNb, nbCours: events.length - autresNb };
}

// Rend le panneau "Service déclaré" pour l'enseignant sélectionné.
function renderTeacherService(teacherName) {
    const box = document.getElementById('teacher-service-box');
    if (!box) return;
    if (!teacherName) {
        box.innerHTML = '<div style="font-size:0.8rem; color:var(--text-muted);">Sélectionnez un enseignant.</div>';
        return;
    }

    const svc = getTeacherService(teacherName);
    const compute = computeTeacherHETD(teacherName);
    const plannedHETD = compute.hetdCours;
    const heuresAutres = compute.heuresAutres;
    const nbAutres = compute.nbAutres;
    const nbCours = compute.nbCours;
    const delta = Math.round((plannedHETD - svc.hetd) * 10) / 10;
    const statusColor = delta > 15 ? '#fb7185' : (delta < -15 ? '#fbbf24' : '#34d399');
    const statusLabel = delta > 15 ? 'Heures sup' : (delta < -15 ? 'Sous-service' : 'Équilibré');
    const modeName = MODE_LABELS[svc.mode] || MODE_LABELS.CUSTOM;
    const safe = String(teacherName).replace(/'/g, "\\'");

    box.innerHTML = `
        <div style="font-size:0.8rem; font-weight:600; margin-bottom:8px;">${teacherName}</div>
        <div style="display:flex; flex-direction:column; gap:8px;">
            <label style="font-size:0.75rem; color:var(--text-muted);">Type de service</label>
            <div style="display:flex; gap:6px; flex-wrap:wrap;">
                ${['PLAIN','DEMI','CUSTOM'].map(m => `
                    <button class="btn ${svc.mode===m?'btn-primary':''}" style="padding:0.3rem 0.6rem; font-size:0.72rem;"
                        onclick="setTeacherServiceMode('${safe}','${m}')">${MODE_LABELS[m]}</button>
                `).join('')}
            </div>
            <label style="font-size:0.72rem; color:var(--text-muted); margin-top:4px;">
                Heures Équivalent TD (HETD) du service :
            </label>
            <input type="number" id="teacher-svc-hetd" value="${svc.hetd}" min="0" step="1"
                onchange="setTeacherServiceHETD('${safe}')" style="width:110px; padding:0.3rem 0.5rem;" />
            <div style="font-size:0.75rem; color:var(--text-muted); margin-top:6px;">
                Mode actuel : <strong>${modeName}</strong> · HETD : <strong>${svc.hetd} h</strong>
            </div>
            <div style="margin-top:8px; border-top:1px solid var(--border-color); padding-top:8px;">
                <div style="font-size:0.75rem; color:var(--text-muted);">Bilan planifié (HETD) :</div>
                <div style="display:flex; justify-content:space-between; font-size:0.85rem;">
                    <span>Planifié (cours)</span><strong>${plannedHETD} h</strong>
                </div>
                <div style="display:flex; justify-content:space-between; font-size:0.85rem; color:${statusColor};">
                    <span>Δ vs service</span><strong>${delta>0?'+':''}${delta} h (${statusLabel})</strong>
                </div>
            </div>
            <div style="margin-top:8px; border-top:1px dashed var(--border-color); padding-top:8px;">
                <div style="font-size:0.75rem; color:var(--text-muted); font-weight:600;">Autre (hors cours / HETD)</div>
                <div style="display:flex; justify-content:space-between; font-size:0.85rem; color:var(--text-muted);">
                    <span>Réunions / co-encadrements (${nbAutres})</span><strong>${heuresAutres} h</strong>
                </div>
            </div>
        </div>`;
}
// Définit le mode de service (PLAIN/DEMI/CUSTOM) et ajuste le HETD par défaut.
function setTeacherServiceMode(teacherName, mode) {
    const current = getTeacherService(teacherName);
    let hetd = current.hetd;
    if (mode === 'PLAIN') hetd = SERVICE_PLAIN_HETD;
    else if (mode === 'DEMI') hetd = SERVICE_DEMI_HETD;
    teacherServices[teacherName] = { mode: mode, hetd: hetd };
    renderTeacherService(teacherName);
}

// Met à jour le HETD (custom) depuis le champ.
function setTeacherServiceHETD(teacherName) {
    const el = document.getElementById('teacher-svc-hetd');
    if (!el) return;
    const val = parseFloat(el.value);
    const mode = getTeacherService(teacherName).mode;
    if (!isNaN(val)) {
        teacherServices[teacherName] = { mode: mode, hetd: val };
    }
    renderTeacherService(teacherName);
}

// Sauvegarde les services déclarés via l'API.
async function saveTeacherServices() {
    const res = await fetch('/api/v1/admin/teacher-services', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ services: teacherServices })
    });
    return res.json();
}

// Enrichit loadTeacherMatrix (définie dans app.js) pour rendre le panneau service.
const _origLoadTeacherMatrix = window.loadTeacherMatrix;
if (typeof _origLoadTeacherMatrix === 'function') {
    window.loadTeacherMatrix = function (...args) {
        const r = _origLoadTeacherMatrix.apply(this, args);
        const sel = document.getElementById('admin-select-teacher');
        renderTeacherService(sel ? sel.value : '');
        return r;
    };
}

// Enrichit filterAdminTeacherList (avec flag pour re-rendre le service).
const _origFilterAdmin = window.filterAdminTeacherList;
if (typeof _origFilterAdmin === 'function') {
    window.filterAdminTeacherList = function (refreshService) {
        const r = _origFilterAdmin.apply(this, arguments);
        const sel = document.getElementById('admin-select-teacher');
        if (refreshService !== false && sel) renderTeacherService(sel.value);
        return r;
    };
}

// Sauvegarde les services lors de l'enregistrement des contraintes (bouton global).
async function saveAllServicesSilent() {
    try { await saveTeacherServices(); } catch (e) {}
}

// Charge les services au démarrage puis re-rend sur l'enseignant sélectionné.
document.addEventListener('DOMContentLoaded', () => {
    loadTeacherServices().then(() => {
        const sel = document.getElementById('admin-select-teacher');
        if (sel) renderTeacherService(sel.value || '');
    });
});