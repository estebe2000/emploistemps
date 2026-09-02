/*
 * Changer d'enseignant : suggestions intelligentes des enseignants LIBRES sur le créneau,
 * identification claire des enseignants occupés et génération de mail type pour le responsable EDT.
 */

// Génère le texte de mail pour un changement d'enseignant.
function buildTeacherMail(ev, newTeacher, isAvailable, occDetail) {
    const r = (typeof getWeekDateRange === 'function') ? getWeekDateRange(ev.week || 1) : null;
    const weekLabel = r ? `Semaine ISO ${r.iso} (${r.label})` : `Semaine ${ev.week}`;
    const slotTime = ev.slot_time || MOVE_SLOT_TIMES[ev.slot_idx] || '';
    
    let dispoNote = "• Disponibilité : Collègue 100% disponible sur ce créneau (aucun conflit EDT détecté).";
    if (isAvailable === false) {
        dispoNote = `• ⚠️ Attention : Collègue actuellement occupé (${occDetail || 'autre cours programmé'}). Une permutation ou ajustement sera nécessaire.`;
    }

    const lines = [
        "Bonjour,",
        "",
        "Je souhaite modifier l'enseignant du cours suivant :",
        "",
        `• Cours : ${ev.resource_name} (${ev.resource_code || ''})`,
        `• Groupe : ${ev.group_id}`,
        `• Enseignant actuel : ${ev.teacher_name}`,
        `• Créneau : ${weekLabel} - ${ev.day} ${slotTime}`,
        `• Salle : ${ev.room_name}`,
        "",
        "Proposition de remplacement :",
        "",
        `• Nouvel enseignant pressenti : ${newTeacher}`,
        dispoNote,
        "",
        "Merci de confirmer la faisabilité et de mettre à jour l'emploi du temps.",
        "Cordialement."
    ];
    return lines.join("\n");
}

function copyTeacherMail() {
    const ta = document.getElementById('teacher-mail-text');
    if (!ta || !ta.value) return;
    ta.select();
    try { document.execCommand('copy'); } catch (e) {}
    if (navigator.clipboard) navigator.clipboard.writeText(ta.value).catch(()=>{});
    alert('📋 Demande de changement d\'enseignant copiée dans le presse-papiers.');
}

// Analyse la disponibilité de chaque enseignant sur le créneau du cours `ev`
function getTeachersAvailability(ev) {
    const events = currentSchedule || [];
    const allTeachers = dataset.teachers || [];
    const evDate = ev.date;

    const slotEvents = events.filter(o => {
        if (o.lesson_id === ev.lesson_id) return false;
        if (evDate && o.date) return o.date === evDate && o.slot_idx === ev.slot_idx;
        return o.week === ev.week && o.day_idx === ev.day_idx && o.slot_idx === ev.slot_idx;
    });

    const freeList = [];
    const busyList = [];

    allTeachers.forEach(t => {
        const isCurrent = typeof areTeachersConflicting === 'function' ? areTeachersConflicting(t.name, ev.teacher_name) : (t.name.toLowerCase() === (ev.teacher_name || '').toLowerCase());
        
        const conflict = slotEvents.find(o => typeof areTeachersConflicting === 'function' ? areTeachersConflicting(t.name, o.teacher_name) : (t.name.toLowerCase() === (o.teacher_name || '').toLowerCase()));

        if (conflict) {
            busyList.push({
                name: t.name,
                statut: t.statut || '',
                isCurrent,
                available: false,
                conflictDesc: `${conflict.resource_code || conflict.resource_name} (${conflict.group_id} - ${conflict.room_name || ''})`
            });
        } else {
            freeList.push({
                name: t.name,
                statut: t.statut || '',
                isCurrent,
                available: true,
                conflictDesc: ''
            });
        }
    });

    freeList.sort((a, b) => a.name.localeCompare(b.name, 'fr', { sensitivity: 'base' }));
    busyList.sort((a, b) => a.name.localeCompare(b.name, 'fr', { sensitivity: 'base' }));

    return { freeList, busyList };
}

// Surcharge openChangeTeacherModal (app.js) : peuple avec statut de disponibilité et pré-remplit le mail
const _origOCT = window.openChangeTeacherModal;
if (typeof _origOCT === 'function') {
    window.openChangeTeacherModal = function (...args) {
        document.getElementById('context-menu').style.display = 'none';
        if (!selectedLessonId) return;
        const ev = currentSchedule.find(e => e.lesson_id === selectedLessonId);
        if (!ev) return;

        document.getElementById('change-teacher-lesson-title').textContent = `${ev.resource_name} (${ev.group_id}) — ${ev.day} ${ev.slot_time || ''} | Actuel : ${ev.teacher_name}`;

        const sel = document.getElementById('change-target-teacher');
        sel.innerHTML = '';

        const { freeList, busyList } = getTeachersAvailability(ev);

        // Groupe 1 : Enseignants Libres
        if (freeList.length > 0) {
            const grpFree = document.createElement('optgroup');
            grpFree.label = `✨ Enseignants LIBRES sur ce créneau (${freeList.length})`;
            freeList.forEach(t => {
                const opt = document.createElement('option');
                opt.value = t.name;
                opt.textContent = `🟢 ${t.name} (${t.statut || 'Enseignant'}) — LIBRE`;
                if (t.isCurrent) opt.selected = true;
                opt.setAttribute('data-available', 'true');
                grpFree.appendChild(opt);
            });
            sel.appendChild(grpFree);
        }

        // Groupe 2 : Enseignants Occupés
        if (busyList.length > 0) {
            const grpBusy = document.createElement('optgroup');
            grpBusy.label = `⚠️ Enseignants OCCUPÉS sur ce créneau (${busyList.length})`;
            busyList.forEach(t => {
                const opt = document.createElement('option');
                opt.value = t.name;
                opt.textContent = `🔴 ${t.name} — OCCUPÉ (${t.conflictDesc})`;
                if (t.isCurrent) opt.selected = true;
                opt.setAttribute('data-available', 'false');
                opt.setAttribute('data-conflict', t.conflictDesc);
                grpBusy.appendChild(opt);
            });
            sel.appendChild(grpBusy);
        }

        const refresh = () => {
            const opt = sel.options[sel.selectedIndex];
            const tName = sel.value || ev.teacher_name;
            const isAvail = opt ? opt.getAttribute('data-available') === 'true' : true;
            const conflictDetail = opt ? opt.getAttribute('data-conflict') : '';
            document.getElementById('teacher-mail-text').value = buildTeacherMail(ev, tName, isAvail, conflictDetail);
        };

        sel.onchange = refresh;
        refresh();

        document.getElementById('change-teacher-modal').style.display = 'flex';
    };
}

// Surcharge confirmChangeTeacher : génère + copie le mail, informe l'utilisateur
const _origCCT = window.confirmChangeTeacher;
if (typeof _origCCT === 'function') {
    window.confirmChangeTeacher = async function () {
        const ev = currentSchedule.find(e => e.lesson_id === selectedLessonId);
        if (!ev) return;
        const sel = document.getElementById('change-target-teacher');
        const opt = sel ? sel.options[sel.selectedIndex] : null;
        const newTeacher = sel ? sel.value : '';
        if (!newTeacher) { alert("Veuillez sélectionner un enseignant."); return; }

        const isAvail = opt ? opt.getAttribute('data-available') === 'true' : true;
        const conflictDetail = opt ? opt.getAttribute('data-conflict') : '';
        document.getElementById('teacher-mail-text').value = buildTeacherMail(ev, newTeacher, isAvail, conflictDetail);
        
        copyTeacherMail();
        alert(`📋 Demande de remplacement par ${newTeacher} générée et copiée dans le presse-papiers.`);
    };
}