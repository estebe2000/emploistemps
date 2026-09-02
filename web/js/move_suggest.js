/*
 * Déplacement de cours : suggestions intelligentes avec scoring d'ergonomie et compacité
 * (anti-trous, anti-déplacement pour 1 cours, respect strict de l'arbre des groupes et des quotas admin).
 * Génération de mails simples (créneau libre direct) et complexes (permutations de cours).
 */

const MOVE_SLOT_TIMES = {
    0: "08:00 - 09:30", 1: "09:30 - 11:00", 2: "11:00 - 12:30",
    3: "13:30 - 15:00", 4: "15:00 - 16:30", 5: "16:30 - 18:00"
};
const MOVE_DAYS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"];
const MOVE_FORBIDDEN = [("Jeudi_3"), ("Jeudi_4"), ("Jeudi_5"), ("Samedi_3"), ("Samedi_4"), ("Samedi_5")];

function _normTeacher(name) {
    if (!name) return '';
    return name.replace(/\b(m\.|mme|dr|pr|prof)\b\.?/gi, '').replace(/\s+/g, ' ').trim().toLowerCase();
}

function areTeachersConflicting(t1, t2) {
    if (!t1 || !t2) return false;
    const n1 = _normTeacher(t1);
    const n2 = _normTeacher(t2);
    if (n1 === n2 || n1.includes(n2) || n2.includes(n1)) return true;
    const parts1 = n1.split(',').map(s=>s.trim()).filter(Boolean);
    const parts2 = n2.split(',').map(s=>s.trim()).filter(Boolean);
    for (const p1 of parts1) {
        for (const p2 of parts2) {
            if (p1 === p2 || (p1.length > 3 && p2.includes(p1)) || (p2.length > 3 && p1.includes(p2))) return true;
        }
    }
    return false;
}

function getGroupHierarchy(groupId) {
    const g = String(groupId || '').toUpperCase().trim();
    const set = new Set([g]);
    if (!g) return set;

    // BUT 1
    if (g.includes('BUT1') || g.includes('TD') || g.includes('TP')) {
        if (g.includes('BUT1_PROMO')) {
            ['BUT1_PROMO', 'TD1', 'TD2', 'TD3', 'TD4', 'TD5',
             'TP1A', 'TP1B', 'TP2A', 'TP2B', 'TP3A', 'TP3B', 'TP4A', 'TP4B', 'TP5A', 'TP5B'].forEach(x=>set.add(x));
        }
        for (let i = 1; i <= 5; i++) {
            if (g.includes('TD' + i)) {
                ['BUT1_PROMO', 'TD' + i, 'TP' + i + 'A', 'TP' + i + 'B'].forEach(x=>set.add(x));
            }
            if (g.includes('TP' + i + 'A') || g.includes('TP' + i + 'B')) {
                ['BUT1_PROMO', 'TD' + i, g].forEach(x=>set.add(x));
            }
        }
    }
    // BUT 2 (TC2)
    if (g.includes('TC2') || g.includes('BUT2')) {
        if (g.includes('PROMO')) {
            ['TC2_PROMO', 'TC2_G1', 'TC2_G2', 'TC2_G3', 'TC2_G1_BDMRC', 'TC2_G2_MDEE', 'TC2_G3_MMPV'].forEach(x=>set.add(x));
        }
        if (g.includes('G1')) ['TC2_PROMO', 'TC2_G1', 'TC2_G1_BDMRC', 'TC2_G1A_BDMRC', 'TC2_G1B_BDMRC'].forEach(x=>set.add(x));
        if (g.includes('G2')) ['TC2_PROMO', 'TC2_G2', 'TC2_G2_MDEE', 'TC2_G2A_MDEE', 'TC2_G2B_MDEE'].forEach(x=>set.add(x));
        if (g.includes('G3')) ['TC2_PROMO', 'TC2_G3', 'TC2_G3_MMPV', 'TC2_G3A_MMPV', 'TC2_G3B_MMPV'].forEach(x=>set.add(x));
    }
    // BUT 3 (TC3)
    if (g.includes('TC3') || g.includes('BUT3')) {
        if (g.includes('PROMO')) {
            ['TC3_PROMO', 'TC3_G1', 'TC3_G2', 'TC3_G3', 'TC3_FI_G1_BDMRC', 'TC3_FA_G1_BDMRC', 'TC3_FI_G3_MMPV'].forEach(x=>set.add(x));
        }
        if (g.includes('G1')) ['TC3_PROMO', 'TC3_G1', 'TC3_FI_G1_BDMRC', 'TC3_FA_G1_BDMRC', 'TC3_FI_G1A_BDMRC', 'TC3_FI_G1B_BDMRC'].forEach(x=>set.add(x));
        if (g.includes('G3')) ['TC3_PROMO', 'TC3_G3', 'TC3_FI_G3_MMPV', 'TC3_FI_G3A_MMPV', 'TC3_FI_G3B_MMPV'].forEach(x=>set.add(x));
    }
    return set;
}

function areGroupsConflicting(g1, g2, m1, m2) {
    if (m1 && m2 && Array.isArray(m1) && Array.isArray(m2)) {
        if (m1.some(x => m2.includes(x))) return true;
    }
    const h1 = getGroupHierarchy(g1);
    if (m1 && Array.isArray(m1)) m1.forEach(x=>h1.add(x));
    const h2 = getGroupHierarchy(g2);
    if (m2 && Array.isArray(m2)) m2.forEach(x=>h2.add(x));
    for (const item of h1) {
        if (h2.has(item)) return true;
    }
    return false;
}

function getDayDateLabel(week, dIdx) {
    if (typeof getWeekDateRange === 'function') {
        try {
            const r = getWeekDateRange(week || 1);
            const base = new Date(r.start);
            base.setDate(base.getDate() + dIdx);
            const jours = ["dim.","lun.","mar.","mer.","jeu.","ven.","sam."];
            const mois = ["janv.","févr.","mars","avr.","mai","juin","juil.","août","sept.","oct.","nov.","déc."];
            return `${jours[base.getDay()]} ${base.getDate()} ${mois[base.getMonth()]} ${base.getFullYear()}`;
        } catch (e) {}
    }
    return MOVE_DAYS[dIdx] || '';
}

function getTargetDateIso(week, dIdx) {
    if (typeof getWeekDateRange === 'function') {
        try {
            const r = getWeekDateRange(week || 1);
            const base = new Date(r.start);
            base.setDate(base.getDate() + dIdx);
            return base.toISOString().split('T')[0];
        } catch (e) {}
    }
    return '';
}

// Calcul du score de continuité et d'anti-trous
function calculateSlotScore(ev, targetWeek, dIdx, s, events) {
    const targetDate = getTargetDateIso(targetWeek, dIdx);
    const dayGroupSlots = [];
    const dayTeacherSlots = [];

    events.forEach(o => {
        const sameDay = (targetDate && o.date === targetDate) || (o.week === targetWeek && o.day_idx === dIdx);
        if (!sameDay || o.lesson_id === ev.lesson_id) return;
        if (areGroupsConflicting(ev.group_id, o.group_id, ev.matching_groups, o.matching_groups)) {
            dayGroupSlots.push(o.slot_idx);
        }
        if (areTeachersConflicting(ev.teacher_name, o.teacher_name)) {
            dayTeacherSlots.push(o.slot_idx);
        }
    });

    if (dayGroupSlots.length === 0) {
        return {
            score: -80,
            badge: "⚠️ Seul cours du jour",
            badgeClass: "badge-isolated",
            desc: "Les étudiants n'ont aucun autre cours ce jour-là."
        };
    }

    const hasPrev = dayGroupSlots.includes(s - 1);
    const hasNext = dayGroupSlots.includes(s + 1);

    if (hasPrev && hasNext) {
        return {
            score: 100,
            badge: "🟡 Comble une pause",
            badgeClass: "badge-fill",
            desc: `Comble parfaitement la pause entre ${MOVE_SLOT_TIMES[s-1]} et ${MOVE_SLOT_TIMES[s+1]}.`
        };
    }

    if (hasPrev || hasNext) {
        let sc = 60;
        if (dayTeacherSlots.length > 0) sc += 20;
        return {
            score: sc,
            badge: "🟢 Enchaînement direct",
            badgeClass: "badge-direct",
            desc: "Collé à un cours existant (0 temps mort pour les étudiants)."
        };
    }

    const dists = dayGroupSlots.map(x => Math.abs(x - s));
    const minDist = Math.min(...dists);
    return {
        score: 10 - (minDist * 25),
        badge: "⚪ Créneau libre",
        badgeClass: "badge-gap",
        desc: `Crée une pause de ${(minDist * 1.5).toFixed(1)}h pour les étudiants.`
    };
}

// Calcul de toutes les suggestions
function computeMoveSuggestions(ev, targetWeek) {
    const tWeek = targetWeek || ev.week || 1;
    const suggestions = [];
    const permutations = [];
    const events = currentSchedule || [];
    const rooms = dataset.rooms || [];
    const cfgConstraints = window.constraints || {};

    const maxStudH = parseFloat(cfgConstraints.max_hours_per_day_student || 8);
    const maxTeachH = parseFloat(cfgConstraints.max_hours_per_day_teacher || 6);

    let reqRoomType = ev.required_room_type || '';
    const resName = String(ev.resource_name || '').toLowerCase();
    if (!reqRoomType) {
        if (resName.includes('num') || resName.includes('info') || resName.includes('culture num')) reqRoomType = 'TP_INFO';
        else if (ev.event_type === 'CM') reqRoomType = 'AMPHI';
        else if (ev.event_type === 'TP') reqRoomType = 'TP';
        else reqRoomType = 'TD';
    }

    for (let dIdx = 0; dIdx < 6; dIdx++) {
        const dayName = MOVE_DAYS[dIdx];
        const targetDate = getTargetDateIso(tWeek, dIdx);

        for (let s = 0; s < 6; s++) {
            if (dIdx === ev.day_idx && s === ev.slot_idx && tWeek === (ev.week || tWeek)) continue;
            if (MOVE_FORBIDDEN.includes(`${dayName}_${s}`)) continue;

            const slotEvents = events.filter(o => {
                const sameDay = (targetDate && o.date === targetDate) || (o.week === tWeek && o.day_idx === dIdx);
                return sameDay && o.slot_idx === s && o.lesson_id !== ev.lesson_id;
            });

            const teachConflicts = slotEvents.filter(o => areTeachersConflicting(ev.teacher_name, o.teacher_name));
            const groupConflicts = slotEvents.filter(o => areGroupsConflicting(ev.group_id, o.group_id, ev.matching_groups, o.matching_groups));

            // Quotas journaliers
            const dayGroupEvents = events.filter(o => {
                const sameDay = (targetDate && o.date === targetDate) || (o.week === tWeek && o.day_idx === dIdx);
                return sameDay && o.lesson_id !== ev.lesson_id && areGroupsConflicting(ev.group_id, o.group_id, ev.matching_groups, o.matching_groups);
            });
            const dayTeachEvents = events.filter(o => {
                const sameDay = (targetDate && o.date === targetDate) || (o.week === tWeek && o.day_idx === dIdx);
                return sameDay && o.lesson_id !== ev.lesson_id && areTeachersConflicting(ev.teacher_name, o.teacher_name);
            });

            const totalStudH = dayGroupEvents.reduce((acc, o) => acc + (o.duration_hours || 1.5), 0) + (ev.duration_hours || 1.5);
            const totalTeachH = dayTeachEvents.reduce((acc, o) => acc + (o.duration_hours || 1.5), 0) + (ev.duration_hours || 1.5);

            if (totalStudH > maxStudH || totalTeachH > maxTeachH) continue;

            // Salles libres
            const occRoomIds = new Set(slotEvents.map(o => o.room_id).filter(Boolean));
            const freeRooms = rooms.filter(r => !occRoomIds.has(r.id));
            const matchRooms = freeRooms.filter(r => reqRoomType && (r.type || '').includes(reqRoomType));
            const candidateRooms = matchRooms.length > 0 ? matchRooms : freeRooms;
            if (!candidateRooms.length) continue;

            // CAS SIMPLE : Créneau direct libre
            if (teachConflicts.length === 0 && groupConflicts.length === 0) {
                const scoring = calculateSlotScore(ev, tWeek, dIdx, s, events);
                suggestions.push({
                    dIdx, s, dayName, week: tWeek,
                    dateLabel: getDayDateLabel(tWeek, dIdx),
                    slotTime: MOVE_SLOT_TIMES[s],
                    score: scoring.score,
                    badge: scoring.badge,
                    desc: scoring.desc,
                    freeRooms: candidateRooms.slice(0, 3),
                    isPermutation: false
                });
            }
            // CAS COMPLEXE : Permutation possible (1 seul conflit déplaçable)
            else if ((teachConflicts.length + groupConflicts.length) === 1) {
                const conflicting = (teachConflicts.length > 0 ? teachConflicts : groupConflicts)[0];
                permutations.push({
                    dIdx, s, dayName, week: tWeek,
                    dateLabel: getDayDateLabel(tWeek, dIdx),
                    slotTime: MOVE_SLOT_TIMES[s],
                    score: -50,
                    badge: "🔀 Permutation requise",
                    desc: `Nécessite de décaler : ${conflicting.resource_name} (${conflicting.teacher_name})`,
                    freeRooms: candidateRooms.slice(0, 3),
                    conflictingCourse: conflicting,
                    isPermutation: true
                });
            }
        }
    }

    suggestions.sort((a, b) => b.score - a.score);
    return { suggestions: suggestions.slice(0, 15), permutations: permutations.slice(0, 5) };
}

// Générateur de mail simple (créneau libre direct)
function buildMoveMailSimple(ev, targetWeek, dayName, slotIdx, roomId, roomName, suggestion) {
    const curR = (typeof getWeekDateRange === 'function') ? getWeekDateRange(ev.week || 1) : null;
    const curWeekLabel = curR ? `Semaine ISO ${curR.iso} (${curR.label})` : `Semaine ${ev.week}`;
    const newDateLabel = getDayDateLabel(targetWeek, MOVE_DAYS.indexOf(dayName));
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
        "Proposition de nouveau créneau (100% libre) :",
        "",
        `• Nouveau créneau : ${newWeekLabel} - ${newDateLabel} ${MOVE_SLOT_TIMES[slotIdx] || ''} - Salle ${roomName || roomId}`,
        `• Confort pédagogique : ${suggestion?.desc || 'Créneau sans conflit ni trou pour les étudiants.'}`,
        "",
        "Merci de confirmer la disponibilité et de mettre à jour l'emploi du temps.",
        "Cordialement."
    ];
    return lines.join("\n");
}

// Générateur de mail complexe (avec permutation)
function buildMoveMailComplex(ev, targetWeek, dayName, slotIdx, roomId, roomName, perm) {
    const curR = (typeof getWeekDateRange === 'function') ? getWeekDateRange(ev.week || 1) : null;
    const curWeekLabel = curR ? `Semaine ISO ${curR.iso}` : `Semaine ${ev.week}`;
    const newDateLabel = getDayDateLabel(targetWeek, MOVE_DAYS.indexOf(dayName));
    const cCourse = perm.conflictingCourse;

    const lines = [
        "Bonjour,",
        "",
        "Dans le cadre d'un besoin de reprogrammation, voici une proposition de permutation optimisée :",
        "",
        "1️⃣ Cours principal à déplacer :",
        `• Cours : ${ev.resource_name} (${ev.group_id})`,
        `• Enseignant : ${ev.teacher_name}`,
        `• Actuellement : ${curWeekLabel} - ${ev.day} ${MOVE_SLOT_TIMES[ev.slot_idx] || ''} (Salle ${ev.room_name})`,
        `• Nouveau créneau visé : ${newDateLabel} ${MOVE_SLOT_TIMES[slotIdx] || ''} (Salle ${roomName || roomId})`,
        "",
        "2️⃣ Permutation / Ajustement nécessaire :",
        `• Le cours « ${cCourse.resource_name} » (Enseignant : ${cCourse.teacher_name}, Groupe : ${cCourse.group_id}) actuellement prévu sur ce créneau doit être décalé vers un créneau de repli compatible.`,
        "",
        "3️⃣ Respect des règles :",
        "• Quotas journaliers d'heures respectés pour tous les étudiants et enseignants.",
        "• Continuité pédagogique préservée.",
        "",
        "Merci de bien vouloir valider cette opération sur Hyperplanning.",
        "Cordialement."
    ];
    return lines.join("\n");
}

// Remplit la modale de déplacement
async function populateMoveModal(ev) {
    const suggestList = document.getElementById('move-suggest-list');
    if (!suggestList) return;
    window._moveBaseWeek = ev.week || 1;
    if (window._moveTargetWeek === undefined) window._moveTargetWeek = window._moveBaseWeek;
    const tWeek = window._moveTargetWeek;

    suggestList.innerHTML = '<div style="padding:10px; color:var(--text-muted); font-size:0.8rem;">Calcul des créneaux optimisés en cours...</div>';

    let sug = [];
    let perm = [];

    try {
        const res = await fetch(`/api/v1/schedule/suggest-move?lesson_id=${encodeURIComponent(ev.lesson_id)}&target_week=${tWeek}`);
        if (res.ok) {
            const data = await res.json();
            sug = data.suggestions || [];
            perm = data.permutations || [];
        } else {
            const localRes = computeMoveSuggestions(ev, tWeek);
            sug = localRes.suggestions || [];
            perm = localRes.permutations || [];
        }
    } catch (e) {
        const localRes = computeMoveSuggestions(ev, tWeek);
        sug = localRes.suggestions || [];
        perm = localRes.permutations || [];
    }

    suggestList.innerHTML = '';

    // Bandeau Quotas & Navigation
    const nav = document.createElement('div');
    nav.style.cssText = 'display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; margin-bottom:10px; background:rgba(255,255,255,0.02); border:1px solid var(--border-color); border-radius:6px; padding:6px 10px;';
    const r = (typeof getWeekDateRange === 'function') ? getWeekDateRange(tWeek) : null;
    const wLabel = r ? `Semaine ISO ${r.iso} (${r.label})` : `Semaine ${tWeek}`;
    nav.innerHTML = `
        <div style="display:flex; gap:6px; align-items:center;">
            <span style="font-size:0.75rem; color:var(--text-muted);">Semaine cible :</span>
            <button class="btn" style="padding:2px 8px;" onclick="movePrevWeek()">◀</button>
            <span style="font-size:0.82rem; font-weight:700; color:#60a5fa;">${wLabel}</span>
            <button class="btn" style="padding:2px 8px;" onclick="moveNextWeek()">▶</button>
        </div>
        <div style="font-size:0.72rem; color:var(--text-muted);">
            ⚖️ Quotas : Max ${window.constraints?.max_hours_per_day_student || 8}h/j étudiants · ${window.constraints?.max_hours_per_day_teacher || 6}h/j prof
        </div>
    `;
    suggestList.appendChild(nav);

    if (!sug.length && !perm.length) {
        const empty = document.createElement('div');
        empty.style.cssText = 'color:#fb7185; font-size:0.8rem; padding:12px; background:rgba(239,68,68,0.1); border-radius:6px;';
        empty.textContent = '❌ Aucun créneau compatible trouvé sur cette semaine (quotas dépassés, prof/groupe/salle occupés ou IUT fermé). Essayez la semaine suivante.';
        suggestList.appendChild(empty);
        return;
    }

    // 1. Propositions directes 100% libres
    if (sug.length > 0) {
        const title = document.createElement('div');
        title.style.cssText = 'font-size:0.75rem; font-weight:700; color:#4ade80; margin:6px 0 4px;';
        title.textContent = `✨ Créneaux 100% libres & optimisés (${sug.length}) :`;
        suggestList.appendChild(title);

        sug.forEach(s => {
            const btn = document.createElement('button');
            btn.className = 'btn';
            btn.style.cssText = 'text-align:left; display:flex; flex-direction:column; gap:3px; width:100%; margin-bottom:6px; padding:8px 10px; border-left:3px solid #4ade80;';
            btn.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center; width:100%;">
                    <span style="font-size:0.82rem; font-weight:600;">🗓️ ${s.dateLabel} · ${s.slotTime}</span>
                    <span style="font-size:0.72rem; font-weight:600; padding:2px 6px; border-radius:4px; background:rgba(74,222,128,0.15); color:#4ade80;">${s.badge}</span>
                </div>
                <div style="font-size:0.72rem; color:var(--text-muted); display:flex; justify-content:space-between; width:100%;">
                    <span>📍 Salles libres : ${s.freeRooms.map(r=>r.name).join(', ')}</span>
                    <span style="font-size:0.7rem; color:#9ca3af;">${s.desc}</span>
                </div>
            `;
            btn.onclick = () => {
                document.getElementById('move-target-day').value = s.dayName;
                document.getElementById('move-target-slot').value = s.s;
                const roomSel = document.getElementById('move-target-room');
                for (let i = 0; i < roomSel.options.length; i++) {
                    if (roomSel.options[i].value === s.freeRooms[0].id) { roomSel.selectedIndex = i; break; }
                }
                window._moveTargetWeek = s.week;
                window._selectedSuggestion = s;
                window._isPermutation = false;
                refreshMoveMail(ev);
                suggestList.querySelectorAll('button[data-sug]').forEach(b => b.classList.remove('btn-primary'));
                btn.classList.add('btn-primary');
            };
            btn.setAttribute('data-sug', '1');
            suggestList.appendChild(btn);
        });
    }

    // 2. Propositions avec permutation
    if (perm.length > 0) {
        const titlePerm = document.createElement('div');
        titlePerm.style.cssText = 'font-size:0.75rem; font-weight:700; color:#fbbf24; margin:12px 0 4px;';
        titlePerm.textContent = `🔀 Alternatives avec permutation (${perm.length}) :`;
        suggestList.appendChild(titlePerm);

        perm.forEach(p => {
            const btn = document.createElement('button');
            btn.className = 'btn';
            btn.style.cssText = 'text-align:left; display:flex; flex-direction:column; gap:3px; width:100%; margin-bottom:6px; padding:8px 10px; border-left:3px solid #fbbf24; background:rgba(245,158,11,0.04);';
            btn.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center; width:100%;">
                    <span style="font-size:0.82rem; font-weight:600;">🗓️ ${p.dateLabel} · ${p.slotTime}</span>
                    <span style="font-size:0.72rem; font-weight:600; padding:2px 6px; border-radius:4px; background:rgba(245,158,11,0.2); color:#fbbf24;">${p.badge}</span>
                </div>
                <div style="font-size:0.72rem; color:var(--text-muted); width:100%;">
                    ⚠️ ${p.desc}
                </div>
            `;
            btn.onclick = () => {
                document.getElementById('move-target-day').value = p.dayName;
                document.getElementById('move-target-slot').value = p.s;
                const roomSel = document.getElementById('move-target-room');
                for (let i = 0; i < roomSel.options.length; i++) {
                    if (roomSel.options[i].value === p.freeRooms[0].id) { roomSel.selectedIndex = i; break; }
                }
                window._moveTargetWeek = p.week;
                window._selectedSuggestion = p;
                window._isPermutation = true;
                refreshMoveMail(ev);
                suggestList.querySelectorAll('button[data-sug]').forEach(b => b.classList.remove('btn-primary'));
                btn.classList.add('btn-primary');
            };
            btn.setAttribute('data-sug', '1');
            suggestList.appendChild(btn);
        });
    }
}

function movePrevWeek() { window._moveTargetWeek = Math.max(1, (window._moveTargetWeek||1) - 1); reopenMoveSuggest(); }
function moveNextWeek() { window._moveTargetWeek = Math.min(15, (window._moveTargetWeek||1) + 1); reopenMoveSuggest(); }

function reopenMoveSuggest() {
    const ev = currentSchedule.find(e => e.lesson_id === selectedLessonId);
    if (!ev) return;
    const suggestList = document.getElementById('move-suggest-list');
    suggestList.innerHTML = '';
    populateMoveModal(ev);
    refreshMoveMail(ev);
}

function refreshMoveMail(ev) {
    const day = document.getElementById('move-target-day').value;
    const slot = parseInt(document.getElementById('move-target-slot').value) || 0;
    const roomSel = document.getElementById('move-target-room');
    const roomId = roomSel.value;
    const roomName = roomSel.options[roomSel.selectedIndex] ? roomSel.options[roomSel.selectedIndex].text : roomId;
    const targetWeek = window._moveTargetWeek || ev.week || 1;
    const sug = window._selectedSuggestion;

    if (window._isPermutation && sug && sug.isPermutation) {
        document.getElementById('move-mail-text').value = buildMoveMailComplex(ev, targetWeek, day, slot, roomId, roomName, sug);
    } else {
        document.getElementById('move-mail-text').value = buildMoveMailSimple(ev, targetWeek, day, slot, roomId, roomName, sug);
    }
}

function copyMoveMail() {
    const ta = document.getElementById('move-mail-text');
    if (!ta || !ta.value) return;
    ta.select();
    try { document.execCommand('copy'); } catch (e) {}
    if (navigator.clipboard) navigator.clipboard.writeText(ta.value).catch(()=>{});
    alert('📋 Texte du mail copié avec succès dans le presse-papiers.');
}

// Surcharge openMoveModal (app.js)
const _origMove = window.openMoveModal;
if (typeof _origMove === 'function') {
    window.openMoveModal = function (...args) {
        const r = _origMove.apply(this, args);
        const ev = currentSchedule.find(e => e.lesson_id === selectedLessonId);
        if (ev) {
            window._selectedSuggestion = null;
            window._isPermutation = false;
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