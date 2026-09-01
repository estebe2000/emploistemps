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