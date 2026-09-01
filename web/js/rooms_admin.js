/*
 * Administration des salles — champs éditables & correction des semaines.
 * Complète app.js : surcharge loadRoomsTable pour rendre Nb places / Informatique /
 * Labo lang éditables (persistance via /api/v1/admin/rooms) et affiche les semaines
 * de fermeture avec leurs dates réelles (getWeekDateRange).
 */

let roomsConfig = {}; // { "<room_id>": { nb_places, informatique, labo_lang } }

// Charge la config éitable des salles depuis le backend.
async function loadRoomsConfig() {
    try {
        const r = await fetch('/api/v1/admin/rooms');
        roomsConfig = (await r.json()) || {};
    } catch (e) {
        roomsConfig = {};
    }
    return roomsConfig;
}

// Renvoie les infos effectives d'une salle (config éditée sinon dataset).
function getRoomInfo(roomId, datasetRoom) {
    const cfg = roomsConfig[roomId] || {};
    const eq = (datasetRoom.equipments || []).map(x => String(x).toUpperCase());
    return {
        nb_places: cfg.nb_places !== undefined && cfg.nb_places !== '' ? cfg.nb_places : (datasetRoom.capacity ?? ''),
        informatique: cfg.informatique !== undefined ? !!cfg.informatique : (eq.includes('COMPUTERS') || eq.includes('POSTES')),
        labo_lang: cfg.labo_lang !== undefined ? !!cfg.labo_lang : (datasetRoom.type === 'TP_LANG' || eq.includes('HEADSETS')),
    };
}

// Surcharge loadRoomsTable (app.js) pour rendre les colonnes éditables + dates de semaines.
const _origRoomsTable = window.loadRoomsTable;
if (typeof _origRoomsTable === 'function') {
    window.loadRoomsTable = async function () {
        const tbody = document.getElementById('rooms-table-body');
        if (!tbody) return;
        tbody.innerHTML = '';
        await loadRoomsConfig();

        (dataset.rooms || []).forEach(r => {
            const closures = (constraints.room_closures_or_reservations || []).filter(c => c.room_id === r.id);
            const info = getRoomInfo(r.id, r);
            // Correction des semaines : affiche le numéro ISO réel + date de la semaine.
            const closureText = closures.length > 0
                ? closures.map(c => `🔴 Sem. ISO ${fmtWeekISO(c.week)} (${fmtWeekShort(c.week)}) ${c.day}${c.reason?` (${c.reason})`:''}`).join(' · ')
                : '🟢 Disponible';

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td style="font-family:'JetBrains Mono'">${r.id}</td>
                <td style="font-weight:600;">${r.name}</td>
                <td><span class="event-badge badge-td">${r.type}</span></td>
                <td>
                    <input type="number" class="room-cell" data-room="${r.id.replace(/"/g,'&quot;')}" data-field="nb_places"
                        value="${info.nb_places}" min="0" style="width:70px;" onchange="syncRoomCell('${r.id.replace(/'/g,"\\'")}','nb_places')">
                </td>
                <td>
                    <input type="checkbox" class="room-cell" data-room="${r.id.replace(/"/g,'&quot;')}" data-field="informatique"
                        ${info.informatique?'checked':''} onchange="syncRoomCell('${r.id.replace(/'/g,"\\'")}','informatique')">
                </td>
                <td>
                    <input type="checkbox" class="room-cell" data-room="${r.id.replace(/"/g,'&quot;')}" data-field="labo_lang"
                        ${info.labo_lang?'checked':''} onchange="syncRoomCell('${r.id.replace(/'/g,"\\'")}','labo_lang')">
                </td>
                <td style="font-size:0.75rem;">${closureText}</td>
            `;
            tbody.appendChild(tr);
        });
    };
}

// Corrige les semaines : renvoie la plage de dates d'une semaine (via getWeekDateRange de app.js).
function fmtWeekShort(week) {
    if (typeof getWeekDateRange !== 'function') return '';
    try {
        const r = getWeekDateRange(week);
        // ex: "31 août → 6 sept"
        return String(r.label || '');
    } catch (e) { return ''; }
}

// Numéro de semaine ISO réel d'une semaine (via getWeekDateRange).
function fmtWeekISO(week) {
    if (typeof getWeekDateRange !== 'function') return week;
    try {
        const r = getWeekDateRange(week);
        return r && r.iso ? r.iso : week;
    } catch (e) { return week; }
}

// Met à jour roomsConfig depuis un input/checkbox puis sauvegarde (auto-save).
function syncRoomCell(roomId, field) {
    const el = document.querySelector(`[data-room="${roomId}"][data-field="${field}"]`);
    if (!el) return;
    if (!roomsConfig[roomId]) roomsConfig[roomId] = {};
    if (el.type === 'checkbox') roomsConfig[roomId][field] = el.checked;
    else roomsConfig[roomId][field] = el.value;
    saveRoomsConfig();
}

async function saveRoomsConfig() {
    try {
        await fetch('/api/v1/admin/rooms', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ rooms: roomsConfig })
        });
    } catch (e) { /* ignore */ }
}

// Charge la config des salles à l'ouverture de l'admin (via openAdminModal hook).
const _origOpenAdminR = window.openAdminModal;
if (typeof _origOpenAdminR === 'function') {
    window.openAdminModal = function (...args) {
        const r = _origOpenAdminR.apply(this, args);
        loadRoomsConfig().then(() => { if (typeof loadRoomsTable === 'function') loadRoomsTable(); });
        return r;
    };
}

// Initialisation au chargement.
document.addEventListener('DOMContentLoaded', () => {
    loadRoomsConfig();
});
// --- Fermeture ponctuelle : vue calendrier (date début / fin) ---

const DAYS_FR_L = ["Dimanche","Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi"];

// Convertit une date ISO (yyyy-mm-dd) => { week (péd. 1..15), day (Lundi..Samedi), isoWeek }.
function dateToWeekDay(dateStr, SEMESTER_START_FUNC) {
    const d = new Date(dateStr + 'T00:00:00');
    if (isNaN(d)) return null;
    const dayIdx = d.getDay(); // 0=Dim..6=Sam
    const dayNames = ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi"];
    const day = dayIdx >= 1 && dayIdx <= 6 ? dayNames[dayIdx-1] : null;
    // base du semestre : window.SEMESTER_START (exposé par app.js) sinon fallback
    const base = typeof window !== 'undefined' && window.SEMESTER_START ? new Date(window.SEMESTER_START) : new Date(2026, 7, 31);
    const diffDays = Math.round((new Date(d.getFullYear(), d.getMonth(), d.getDate()) - new Date(base.getFullYear(), base.getMonth(), base.getDate())) / 86400000);
    const week = Math.floor(diffDays / 7) + 1;
    let iso = week;
    try {
        if (typeof getWeekDateRange === 'function') iso = getWeekDateRange(week < 1 ? 1 : (week > 15 ? 15 : week)).iso;
        else if (typeof isoWeekOf === 'function') iso = isoWeekOf(d);
    } catch (e) {}
    return { date: dateStr, week, day, iso, dayName: DAYS_FR_L[dayIdx] };
}

function dateISO(d) {
            const p = n => String(n).padStart(2, '0');
            return `${d.getFullYear()}-${p(d.getMonth()+1)}-${p(d.getDate())}`;
        }

// Affiche l'aperçu calendrier de la plage (Du/Au) sélectionnée.
function renderClosureCalendarPreview() {
    const el = document.getElementById('closure-cal-preview');
    if (!el) return;
    const start = document.getElementById('closure-start').value;
    const end = document.getElementById('closure-end').value;
    if (!start || !end) { el.innerHTML = 'Sélectionnez une plage de dates pour afficher l\'aperçu.'; return; }
    const s = new Date(start + 'T00:00:00'), e = new Date(end + 'T00:00:00');
    if (e < s) { el.innerHTML = '<span style="color:#fb7185;">⚠️ La date de fin précède le début.</span>'; return; }
    let tmp = new Date(s), cells = [], count = 0;
    while (tmp <= e) {
        const cs = dateISO(tmp);
        const info = dateToWeekDay(cs, SEMESTER_START);
        const bg = info && info.day !== null ? 'rgba(245,158,11,0.25)' : 'rgba(100,116,139,0.15)';
        const dcol = info && info.day !== null ? '#fbbf24' : 'var(--text-muted)';
        cells.push(`<span title="${info ? info.iso+' · '+info.dayName : ''}" style="display:inline-block; width:46px; text-align:center; margin:2px; padding:4px 0; border-radius:4px; background:${bg}; color:${dcol};">${cs.slice(8,10)}/${cs.slice(5,7)}</span>`);
        count++;
        tmp.setDate(tmp.getDate() + 1);
    }
    const infoStart = dateToWeekDay(start, SEMESTER_START);
    const infoEnd = dateToWeekDay(end, SEMESTER_START);
    el.innerHTML = `<div style="font-weight:600; margin-bottom:6px;">Aperçu (${count} jour${count>1?'s':''})</div>
        <div style="display:flex; flex-wrap:wrap; gap:2px;">${cells.join('')}</div>
        <div style="margin-top:6px; font-size:0.75rem;">${infoStart?'Début : Sem. ISO '+infoStart.iso+' ('+infoStart.dayName+')' : ''}${infoEnd && infoEnd.date!==start?' &nbsp;·&nbsp; Fin : Sem. ISO '+infoEnd.iso+' ('+infoEnd.dayName+')':''}</div>`;
}

// Surcharge addRoomClosure (app.js) : gère une plage de dates (Du/Au) + sauvegarde.
const _origAddClosure = window.addRoomClosure;
if (typeof _origAddClosure === 'function') {
    window.addRoomClosure = async function () {
        const roomId = document.getElementById('closure-room-select').value;
        const reason = document.getElementById('closure-reason').value || "Fermeture";
        const start = document.getElementById('closure-start').value;
        const end = document.getElementById('closure-end').value;
        if (!start || !end) { alert("Veuillez sélectionner une plage de dates (Du / Au)."); return; }
        const s = new Date(start + 'T00:00:00'), e = new Date(end + 'T00:00:00');
        if (e < s) { alert("La date de fin précède le début."); return; }

        if (!constraints.room_closures_or_reservations) constraints.room_closures_or_reservations = [];
        let tmp = new Date(s), n = 0;
        while (tmp <= e) {
            const cs = dateISO(tmp);
            const info = dateToWeekDay(cs);
            if (info && info.day !== null) {
                constraints.room_closures_or_reservations.push({ room_id: roomId, week: info.week, day: info.day, slots: [0,1,2,3], reason, date: cs });
                n++;
            }
            tmp.setDate(tmp.getDate() + 1);
        }
        // Sauvegarde réelle sur le backend (constraints.json).
        try {
            await fetch('/api/v1/admin/constraints', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(constraints)
            });
        } catch (err) { /* ignore */ }
        if (typeof loadRoomsTable === 'function') loadRoomsTable();
        const d1 = dateToWeekDay(start), d2 = dateToWeekDay(end);
        alert(`Fermeture enregistrée pour ${roomId} du ${d1?('Semaine ISO '+d1.iso):start} au ${d2?('Semaine ISO '+d2.iso):end} (${n} jour de cours concerné${n>1?'s':''}).`);
    };
}

// Met à jour l'aperçu à la saisie des dates.
document.addEventListener('DOMContentLoaded', () => {
    const ss = document.getElementById('closure-start');
    const se = document.getElementById('closure-end');
    if (ss && se) {
        ss.addEventListener('change', renderClosureCalendarPreview);
        se.addEventListener('change', renderClosureCalendarPreview);
    }
});