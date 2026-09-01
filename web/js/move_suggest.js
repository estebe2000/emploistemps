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

function _evtBusy(ev, week, dayIdx, slot) {
    // cohérence semaine (ou si l'événement est marqué 'a week' ou non renseigné)
    const evWeek = ev.week || week;
    return evWeek === week && ev.day_idx === dayIdx && ev.slot_idx === slot;
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

// Calcule les créneaux compatibles pour déplacer `ev` dans la semaine `targetWeek`
// (défaut = semaine du cours). Respecte : groupe libre, enseignant libre, salle dispo.
// Jeudi après-midi et Samedi après-midi sont ABSENTS (IUT fermé).
function computeMoveSuggestions(ev, targetWeek) {
    const tWeek = targetWeek || ev.week || 1;
    // Politique : si la semaine cible est close, aucun créneau proposé.
    if (typeof window._policyIsWeekOpen === 'function' && !window._policyIsWeekOpen(tWeek)) {
        return [];
    }
    const suggestions = [];
    const events = currentSchedule || [];
    const rooms = dataset.rooms || [];

    for (let dIdx = 0; dIdx < 6; dIdx++) {
        for (let s = 0; s < 6; s++) {
            if (dIdx === ev.day_idx && s === ev.slot_idx && tWeek === (ev.week || tWeek)) continue;
            const dayName = MOVE_DAYS[dIdx];
            // IUT fermé l'après-midi du jeudi et du samedi => interdits.
            if ((dayName === "Jeudi" && s >= 3) || (dayName === "Samedi" && s >= 3)) continue;
            const groupBusy = events.some(o => _evtBusy(o, tWeek, dIdx, s) && o.group_id === ev.group_id);
            if (groupBusy) continue;
            const teacherBusy = events.some(o => _evtBusy(o, tWeek, dIdx, s) && o.teacher_name === ev.teacher_name);
            if (teacherBusy) continue;
            const freeRooms = rooms.filter(r => !events.some(o => _evtBusy(o, tWeek, dIdx, s) && o.room_id === r.id));
            if (!freeRooms.length) continue;
            suggestions.push({ dIdx, s, dayName, week: tWeek, dateLabel: getDayDateLabel(tWeek, dIdx), slotTime: MOVE_SLOT_TIMES[s], freeRooms: freeRooms.slice(0, 3), isLow: false });
        }
    }
    suggestions.sort((a, b) => (a.dIdx * 10 + a.s) - (b.dIdx * 10 + b.s));
    return suggestions.slice(0, 15);
}

// Génère le texte de mail à partir de l'événement, de la semaine cible et du créneau choisi.
function buildMoveMail(ev, targetWeek, dayName, slotIdx, roomId, roomName) {
    const curR = (typeof getWeekDateRange === 'function') ? getWeekDateRange(ev.week || 1) : null;
    const curWeekLabel = curR ? `Semaine ISO ${curR.iso} (${curR.label})` : `Semaine ${ev.week}`;
    // Date du nouveau créneau : dans la semaine CIBLE (targetWeek), pas la semaine d'origine.
    const newDateLabel = buildSuggestionDateLabel(targetWeek, dayName);
    const newR = (typeof getWeekDateRange === 'function') ? getWeekDateRange(targetWeek) : null;
    const newWeekLabel = newR ? `Semaine ISO ${newR.iso}` : `Semaine ${targetWeek}`;
    const lines = [
        "Bonjour,",
        "",
        "Je souhaite modifier le créneau du cours suivant :",
        "",
        `• Cours : ${ev.resource_name} (${ev.resource_code || ''})`,
        `• Groupe : ${ev.group_id}`,
        `• Enseignant : ${ev.teacher_name}`,
        `• Actuellement : ${curWeekLabel} - ${ev.day} ${MOVE_SLOT_TIMES[ev.slot_idx] || ''} - Salle ${ev.room_name}`,
        "",
        "Proposition de nouveau créneau :",
        "",
        `• Nouveau créneau : ${newWeekLabel} - ${newDateLabel} ${MOVE_SLOT_TIMES[slotIdx] || ''} - Salle ${roomName || roomId}`,
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
    window._moveBaseWeek = ev.week || 1;
    if (window._moveTargetWeek === undefined) window._moveTargetWeek = window._moveBaseWeek;
    const tWeek = window._moveTargetWeek;
    highlightMoveWeekButton();
    const sug = computeMoveSuggestions(ev, tWeek);

    // Bandeau de politique de déplacement
    const policyNote = document.createElement('div');
    policyNote.style.cssText = 'font-size:0.72rem; color:var(--text-muted); background:rgba(99,102,241,0.08); border:1px dashed rgba(99,102,241,0.3); border-radius:6px; padding:6px 8px; margin-bottom:8px;';
    policyNote.innerHTML = '📌 ' + (typeof window._policyMessage === 'function' ? window._policyMessage() : 'Déplacement à demander au gestionnaire EDT avant le jeudi pour la semaine suivante.');
    suggestList.appendChild(policyNote);

    // Barre de navigation : semaines (repousser le cours plus tard si besoin)
    const nav = document.createElement('div');
    nav.style.cssText = 'display:flex; gap:6px; align-items:center; flex-wrap:wrap; margin-bottom:8px;';
    nav.innerHTML = `<span style="font-size:0.78rem; color:var(--text-muted);">Semaine :</span>
        <button class="btn" onclick="movePrevWeek()">◀ Préc.</button>
        <span id="move-week-label" style="font-size:0.85rem; font-weight:600;"></span>
        <button class="btn" onclick="moveNextWeek()">Suiv. ▶</button>
        <button class="btn btn-primary" onclick="moveLaterWeek(3)">Repousser +3 sem.</button>
        <button class="btn btn-primary" onclick="moveLaterWeek(5)">Repousser +5 sem.</button>`;
    suggestList.appendChild(nav);
    const label = document.getElementById('move-week-label');
    const r = (typeof getWeekDateRange === 'function') ? getWeekDateRange(tWeek) : null;
    label.textContent = r ? `ISO ${r.iso} (${r.label})` : `Semaine ${tWeek}`;

    if (!sug.length) {
        const empty = document.createElement('div');
        empty.style.cssText = 'color:#fb7185; font-size:0.8rem;';
        if (typeof window._policyIsWeekOpen === 'function' && !window._policyIsWeekOpen(tWeek)) {
            empty.innerHTML = '🔒 Cette semaine est <strong>close</strong> (délai de demande dépassé : ' + (typeof window._policyMessage === 'function' ? window._policyMessage() : 'avant le jeudi 18h pour la semaine suivante') + '). Choisissez une semaine suivante.';
        } else {
            empty.textContent = 'Aucun créneau compatible dans cette semaine (occupés / IUT fermé). Essayez une autre semaine.';
        }
        suggestList.appendChild(empty);
        return;
    }

    sug.forEach(s => {
        const btn = document.createElement('button');
        btn.className = 'btn';
        btn.style.cssText = 'text-align:left; justify-content:space-between; width:100%;';
        btn.innerHTML = `<span style="font-size:0.78rem;">🗓️ ${s.dateLabel} · ${s.slotTime}</span>
            <span style="font-size:0.72rem; color:var(--text-muted);">${s.freeRooms.map(r=>r.name).join(', ')}</span>`;
        btn.onclick = () => {
            document.getElementById('move-target-day').value = s.dayName;
            document.getElementById('move-target-slot').value = s.s;
            const roomSel = document.getElementById('move-target-room');
            for (let i=0;i<roomSel.options.length;i++){
                if (roomSel.options[i].value === s.freeRooms[0].id) { roomSel.selectedIndex=i; break; }
            }
            window._moveTargetWeek = s.week;
            refreshMoveMail(ev);
            suggestList.querySelectorAll('button[data-sug]').forEach(b=>b.classList.remove('btn-primary'));
            btn.classList.add('btn-primary');
        };
        btn.setAttribute('data-sug', '1');
        suggestList.appendChild(btn);
    });
}

function movePrevWeek() { window._moveTargetWeek = Math.max(1, (window._moveTargetWeek||1) - 1); reopenMoveSuggest(); }
function moveNextWeek() { window._moveTargetWeek = Math.min(15, (window._moveTargetWeek||1) + 1); reopenMoveSuggest(); }
function moveLaterWeek(n) { window._moveTargetWeek = (window._moveTargetWeek||1) + n; reopenMoveSuggest(); }

function highlightMoveWeekButton() {
    const nav = document.querySelector('#move-suggest-list > div');
    if (nav) nav.style.border = '1px solid var(--border-color)';
}

function reopenMoveSuggest() {
    const ev = currentSchedule.find(e => e.lesson_id === selectedLessonId);
    if (!ev) return;
    const suggestList = document.getElementById('move-suggest-list');
    suggestList.innerHTML = '';
    populateMoveModal(ev);
    refreshMoveMail(ev);
}

// Met à jour le textarea mail selon le créneau sélectionné (dans la semaine cible).
function refreshMoveMail(ev) {
    const day = document.getElementById('move-target-day').value;
    const slot = parseInt(document.getElementById('move-target-slot').value) || 0;
    const roomSel = document.getElementById('move-target-room');
    const roomId = roomSel.value;
    const roomName = roomSel.options[roomSel.selectedIndex] ? roomSel.options[roomSel.selectedIndex].text : roomId;
    const targetWeek = window._moveTargetWeek || ev.week || 1;
    document.getElementById('move-mail-text').value = buildMoveMail(ev, targetWeek, day, slot, roomId, roomName);
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