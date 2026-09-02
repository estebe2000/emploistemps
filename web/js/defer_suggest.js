/*
 * À reprogrammer ultérieurement : panneau simple qui prépare un MAIL de demande de
 * reprogrammation (sans suggestions de date) pour le responsable EDT.
 * Aucune modification effective de l'emploi du temps.
 */

// Génère le mail de demande de reprogrammation.
function buildDeferMail(ev, note) {
    const r = (typeof getWeekDateRange === 'function') ? getWeekDateRange(ev.week || 1) : null;
    const weekLabel = r ? `Semaine ISO ${r.iso} (${r.label})` : `Semaine ${ev.week}`;
    const lines = [
        "Bonjour,",
        "",
        "Je souhaite reporter la reprogrammation du cours suivant :",
        "",
        `• Cours : ${ev.resource_name} (${ev.resource_code || ''})`,
        `• Groupe : ${ev.group_id}`,
        `• Enseignant : ${ev.teacher_name}`,
        `• Créneau actuel : ${weekLabel} - ${ev.day} ${ev.slot_time}`,
        `• Salle actuelle : ${ev.room_name}`,
        "",
        "Merci de bien vouloir reprogrammer ce cours sur un prochain créneau disponible.",
        "",
        "Précisions : " + (note || "—"),
        "",
        "Merci de confirmer la nouvelle date.",
        "Cordialement."
    ];
    return lines.join("\n");
}

function closeDeferMailModal() {
    const m = document.getElementById('defer-mail-modal');
    if (m) m.style.display = 'none';
}

function openDeferMailModal() {
    const m = document.getElementById('defer-mail-modal');
    if (m) m.style.display = 'flex';
}

// Surcharge deferSelectedLesson (app.js) : ouvre le panneau de demande, sans modifier le planning.
const _origDefer = window.deferSelectedLesson;
if (typeof _origDefer === 'function') {
    window.deferSelectedLesson = function () {
        document.getElementById('context-menu').style.display = 'none';
        if (!selectedLessonId) return;
        const ev = currentSchedule.find(e => e.lesson_id === selectedLessonId);
        if (!ev) return;
        document.getElementById('defer-mail-lesson-title').textContent = `${ev.resource_name} (${ev.group_id})`;
        openDeferMailModal();
        const refresh = () => {
            const note = document.getElementById('defer-mail-note').value || '';
            document.getElementById('defer-mail-text').value = buildDeferMail(ev, note);
        };
        const noteEl = document.getElementById('defer-mail-note');
        if (noteEl) { noteEl.value = ''; noteEl.oninput = refresh; }
        refresh();
    };
}

function copyDeferMail() {
    const ta = document.getElementById('defer-mail-text');
    if (!ta || !ta.value) return;
    ta.select();
    try { document.execCommand('copy'); } catch (e) {}
    if (navigator.clipboard) navigator.clipboard.writeText(ta.value).catch(()=>{});
    alert('📋 Texte copié dans le presse-papiers.');
}