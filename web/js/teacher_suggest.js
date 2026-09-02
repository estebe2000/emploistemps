/*
 * Changer d'enseignant : génère un texte type mail (demande) à copier/coller pour le
 * responsable EDT. Aucune modification effective de l'emploi du temps.
 */

// Génère le texte de mail pour un changement d'enseignant.
function buildTeacherMail(ev, newTeacher) {
    const r = (typeof getWeekDateRange === 'function') ? getWeekDateRange(ev.week || 1) : null;
    const weekLabel = r ? `Semaine ISO ${r.iso} (${r.label})` : `Semaine ${ev.week}`;
    const lines = [
        "Bonjour,",
        "",
        "Je souhaite modifier l'enseignant du cours suivant :",
        "",
        `• Cours : ${ev.resource_name} (${ev.resource_code || ''})`,
        `• Groupe : ${ev.group_id}`,
        `• Enseignant actuel : ${ev.teacher_name}`,
        `• Créneau : ${weekLabel} - ${ev.day} ${ev.slot_time}`,
        `• Salle : ${ev.room_name}`,
        "",
        "Proposition de changement :",
        "",
        `• Nouvel enseignant : ${newTeacher}`,
        "",
        "Merci de confirmer la disponibilité et de mettre à jour l'emploi du temps.",
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
    alert('📋 Texte copié dans le presse-papiers.');
}

// Surcharge openChangeTeacherModal (app.js) : pré-remplit le mail à l'ouverture.
const _origOCT = window.openChangeTeacherModal;
if (typeof _origOCT === 'function') {
    window.openChangeTeacherModal = function (...args) {
        const r = _origOCT.apply(this, args);
        const ev = currentSchedule.find(e => e.lesson_id === selectedLessonId);
        if (ev) {
            const sel = document.getElementById('change-target-teacher');
            const refresh = () => {
                const t = sel.value || ev.teacher_name;
                document.getElementById('teacher-mail-text').value = buildTeacherMail(ev, t);
            };
            if (sel) sel.onchange = refresh;
            refresh();
        }
        return r;
    };
}

// Surcharge confirmChangeTeacher : génère + copie le mail, NE modifie PAS l'emploi du temps.
const _origCCT = window.confirmChangeTeacher;
if (typeof _origCCT === 'function') {
    window.confirmChangeTeacher = async function () {
        const ev = currentSchedule.find(e => e.lesson_id === selectedLessonId);
        if (!ev) return;
        const sel = document.getElementById('change-target-teacher');
        const newTeacher = sel ? sel.value : '';
        if (!newTeacher) { alert("Veuillez sélectionner un enseignant."); return; }
        document.getElementById('teacher-mail-text').value = buildTeacherMail(ev, newTeacher);
        const ta = document.getElementById('teacher-mail-text');
        if (ta) {
            ta.select();
            try { document.execCommand('copy'); } catch (e) {}
            if (navigator.clipboard) navigator.clipboard.writeText(ta.value).catch(()=>{});
        }
        alert('📋 Demande de changement d\'enseignant générée (mail copié). Aucun changement appliqué : à envoyer au gestionnaire EDT.');
    };
}