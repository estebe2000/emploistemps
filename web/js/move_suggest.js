/*
 * Déplacement de cours : suggestions de créneaux compatibles + génération d'un texte
 * type mail pour le responsable EDT. Complète app.js (surcharge openMoveModal /
 * confirmMoveLesson et fournit copyMoveMail).
 */

const MOVE_SLOT_TIMES = {
    0: "08:00 - 09:30", 1: "09:30 - 11:00", 2: "11:00 - 12:30",
    3: "13:30 - 15:00", 4: "15:00 - 16:30", 5: "16:30 - 18:00"
};
const MOVE_DAYS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"];

function _evtBusy(ev, dayIdx, slot) {
    return ev.day_idx === dayIdx && ev.slot_idx === slot;
}

// Convertit un nom de jour (Lundi..Samedi) en date précise dans la semaine `week`.
function buildSuggestionDateLabel(week, dayName) {
    const idx = MOVE_DAYS.indexOf(dayName);
    if (idx < 0) return dayName || '';
    return getDayDateLabel(week, idx);
}

// Retourne la date précise (par ex. "lun. 31 août 2026") du jour dIdx dans la semaine `week`.
function getDayDateLabel(week, dIdx) {
    if (typeof getWeekDateRange !== 'function') return MOVE_DAYS[dIdx] || '';
    try {
        const r = getWeekDateRange(week || 1);
        const base = new Date(r.start); // lundi de la semaine
        const d = new Date(base);
        d.setDate(d.getDate() + dIdx);
        const jours = ["dim.","lun.","mar.","mer.","jeu.","ven.","sam."];
        const mois = ["janv.","févr.","mars","avr.","mai","juin","juil.","août","sept.","oct.","nov.","déc."];
        return `${jours[d.getDay()]} ${d.getDate()} ${mois[d.getMonth()]} ${d.getFullYear()}`;
    } catch (e) { return MOVE_DAYS[dIdx] || ''; }
}

// Calcule les créneaux compatibles pour déplacer `ev`.
// Respecte : groupe libre, enseignant libre, salle dispo.
function computeMoveSuggestions(ev) {
    const suggestions = [];
    const events = currentSchedule || [];
    const rooms = dataset.rooms || [];

    for (let dIdx = 0; dIdx < 6; dIdx++) {
        for (let s = 0; s < 6; s++) {
            if (dIdx === ev.day_idx && s === ev.slot_idx) continue;
            const groupBusy = events.some(o => _evtBusy(o, dIdx, s) && o.group_id === ev.group_id);
            if (groupBusy) continue;
            const teacherBusy = events.some(o => _evtBusy(o, dIdx, s) && o.teacher_name === ev.teacher_name);
            if (teacherBusy) continue;
            const freeRooms = rooms.filter(r => !events.some(o => _evtBusy(o, dIdx, s) && o.room_id === r.id));
            if (!freeRooms.length) continue;
            const dayName = MOVE_DAYS[dIdx];
            const isLow = (dayName === "Jeudi" && s >= 3) || (dayName === "Samedi" && s >= 3);
            suggestions.push({ dIdx, s, dayName, dateLabel: getDayDateLabel(ev.week, dIdx), slotTime: MOVE_SLOT_TIMES[s], freeRooms: freeRooms.slice(0, 3), isLow });
        }
    }
    suggestions.sort((a, b) => (a.dIdx * 10 + a.s + (a.isLow ? 100 : 0)) - (b.dIdx * 10 + b.s + (b.isLow ? 100 : 0)));
    return suggestions.slice(0, 15);
}

// Génère le texte de mail à partir de l'événement et du créneau choisi.
function buildMoveMail(ev, dayName, slotIdx, roomId, roomName) {
    const r = (typeof getWeekDateRange === 'function') ? getWeekDateRange(ev.week || 1) : null;
    const weekLabel = r ? `Semaine ISO ${r.iso} (${r.label})` : `Semaine ${ev.week}`;
    const lines = [
        "Bonjour,",
        "",
        "Je souhaite modifier le créneau du cours suivant :",
        "",
        `• Cours : ${ev.resource_name} (${ev.resource_code || ''})`,
        `• Groupe : ${ev.group_id}`,
        `• Enseignant : ${ev.teacher_name}`,
        `• Actuellement : ${weekLabel} - ${ev.day} ${MOVE_SLOT_TIMES[ev.slot_idx] || ''} - Salle ${ev.room_name}`,
        "",
        "Proposition de nouveau créneau :",
        "",
        `• Nouveau créneau : ${buildSuggestionDateLabel(ev.week, dayName)} ${MOVE_SLOT_TIMES[slotIdx] || ''} - Salle ${roomName || roomId}`,
        "",
        "Merci de confirmer la disponibilité et de mettre à jour l'emploi du temps.",
        "Cordialement."
    ];
    return lines.join("\n");
}
// Remplit les suggestions + pré-remplit les selects + génère le mail.
function populateMoveModal(ev) {
    const suggestList = document.getElementById('move-suggest-list');
    if (!suggestList) return;
    const sug = computeMoveSuggestions(ev);

    if (!sug.length) {
        suggestList.innerHTML = '<div style="color:var(--text-muted); font-size:0.8rem;">Aucun créneau compatible trouvé (tous occupés / contraintes).</div>';
        return;
    }

    suggestList.innerHTML = '';
    sug.forEach(s => {
        const btn = document.createElement('button');
        btn.className = 'btn';
        btn.style.cssText = 'text-align:left; justify-content:space-between; width:100%;';
        btn.innerHTML = `<span style="font-size:0.78rem;">🗓️ ${s.dateLabel} · ${s.slotTime}</span>
            <span style="font-size:0.72rem; color:var(--text-muted);">${s.freeRooms.map(r=>r.name).join(', ')}${s.isLow?' · (recours)':''}</span>`;
        btn.onclick = () => {
            document.getElementById('move-target-day').value = s.dayName;
            document.getElementById('move-target-slot').value = s.s;
            const roomSel = document.getElementById('move-target-room');
            for (let i=0;i<roomSel.options.length;i++){
                if (roomSel.options[i].value === s.freeRooms[0].id) { roomSel.selectedIndex=i; break; }
            }
            refreshMoveMail(ev);
            suggestList.querySelectorAll('button').forEach(b=>b.classList.remove('btn-primary'));
            btn.classList.add('btn-primary');
        };
        suggestList.appendChild(btn);
    });
}

// Met à jour le textarea mail selon le créneau sélectionné.
function refreshMoveMail(ev) {
    const day = document.getElementById('move-target-day').value;
    const slot = parseInt(document.getElementById('move-target-slot').value) || 0;
    const roomSel = document.getElementById('move-target-room');
    const roomId = roomSel.value;
    const roomName = roomSel.options[roomSel.selectedIndex] ? roomSel.options[roomSel.selectedIndex].text : roomId;
    document.getElementById('move-mail-text').value = buildMoveMail(ev, day, slot, roomId, roomName);
}

function copyMoveMail() {
    const ta = document.getElementById('move-mail-text');
    if (!ta || !ta.value) return;
    ta.select();
    try { document.execCommand('copy'); } catch (e) {}
    if (navigator.clipboard) navigator.clipboard.writeText(ta.value).catch(()=>{});
    alert('📋 Texte copié dans le presse-papiers.');
}

// Surcharge openMoveModal (app.js)
const _origMove = window.openMoveModal;
if (typeof _origMove === 'function') {
    window.openMoveModal = function (...args) {
        const r = _origMove.apply(this, args);
        const ev = currentSchedule.find(e => e.lesson_id === selectedLessonId);
        if (ev) {
            populateMoveModal(ev);
            ['move-target-day','move-target-slot','move-target-room'].forEach(id => {
                const el = document.getElementById(id);
                if (el) el.onchange = () => refreshMoveMail(ev);
            });
            refreshMoveMail(ev);
        }
        return r;
    };
}