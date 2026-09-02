/*
 * Changer de salle : enrichit la modale avec un sélecteur de salle et un texte type mail
 * (copier/coller pour le responsable EDT). Complète app.js.
 */

const ROOM_SLOT_TIMES = {
    0: "08:00 - 09:30", 1: "09:30 - 11:00", 2: "11:00 - 12:30",
    3: "13:30 - 15:00", 4: "15:00 - 16:30", 5: "16:30 - 18:00"
};

// Génère le texte de mail pour un changement de salle.
function buildRoomMail(ev, newRoomId, newRoomName) {
    const r = (typeof getWeekDateRange === 'function') ? getWeekDateRange(ev.week || 1) : null;
    const weekLabel = r ? `Semaine ISO ${r.iso} (${r.label})` : `Semaine ${ev.week}`;
    const lines = [
        "Bonjour,",
        "",
        "Je souhaite modifier la salle du cours suivant :",
        "",
        `• Cours : ${ev.resource_name} (${ev.resource_code || ''})`,
        `• Groupe : ${ev.group_id}`,
        `• Enseignant : ${ev.teacher_name}`,
        `• Créneau : ${weekLabel} - ${ev.day} ${ROOM_SLOT_TIMES[ev.slot_idx] || ''}`,
        `• Salle actuelle : ${ev.room_name}`,
        "",
        "Proposition de changement :",
        "",
        `• Nouvelle salle : ${newRoomName || newRoomId}`,
        "",
        "Merci de confirmer la disponibilité et de mettre à jour l'emploi du temps.",
        "Cordialement."
    ];
    return lines.join("\n");
}

function copyRoomMail() {
    const ta = document.getElementById('room-mail-text');
    if (!ta || !ta.value) return;
    ta.select();
    try { document.execCommand('copy'); } catch (e) {}
    if (navigator.clipboard) navigator.clipboard.writeText(ta.value).catch(()=>{});
    alert('📋 Texte copié dans le presse-papiers.');
}

// Met à jour le mail et le select selon la salle choisie.
function selectRoomForChange(ev, roomId, roomName) {
    const sel = document.getElementById('room-new-slot');
    if (sel) {
        for (let i=0;i<sel.options.length;i++){
            if (sel.options[i].value === roomId) { sel.selectedIndex=i; break; }
        }
    }
    document.getElementById('room-mail-text').value = buildRoomMail(ev, roomId, roomName);
}

// Surcharge confirmRoomChange : génère le texte de DEMANDE (mail) et copie.
// Ne modifie PAS l'emploi du temps (le changement est demandé par mail au gestionnaire).
const _origCRC = window.confirmRoomChange;
if (typeof _origCRC === 'function') {
    window.confirmRoomChange = async function (newRoomId) {
        const ev = currentSchedule.find(e => e.lesson_id === selectedLessonId);
        if (!ev) return;
        const sel = document.getElementById('room-new-slot');
        if (sel) {
            for (let i=0;i<sel.options.length;i++){
                if (sel.options[i].value === newRoomId) { sel.selectedIndex=i; break; }
            }
        }
        const name = (sel && sel.options[sel.selectedIndex]) ? sel.options[sel.selectedIndex].text : newRoomId;
        document.getElementById('room-mail-text').value = buildRoomMail(ev, newRoomId, name);
        // Copie automatiquement le texte de demande (le gestionnaire appliquera).
        const ta = document.getElementById('room-mail-text');
        if (ta) {
            ta.select();
            try { document.execCommand('copy'); } catch (e) {}
            if (navigator.clipboard) navigator.clipboard.writeText(ta.value).catch(()=>{});
        }
        alert('📋 Demande de changement de salle générée (mail copié). Aucun changement appliqué : à envoyer au gestionnaire EDT.');
    };
}

// Charge la modale change-room (surchage openChangeRoomModal) pour peupler select + générer le mail.
const _origCR = window.openChangeRoomModal;
if (typeof _origCR === 'function') {
    window.openChangeRoomModal = function (...args) {
        const r = _origCR.apply(this, args);
        const ev = currentSchedule.find(e => e.lesson_id === selectedLessonId);
        if (ev) {
            const sel = document.getElementById('room-new-slot');
            if (sel) sel.innerHTML = '';
            // Remplit le select avec TOUTES les salles (mise en avant = libres).
            (dataset.rooms || []).forEach(rm => {
                const opt = document.createElement('option');
                opt.value = rm.id;
                opt.textContent = `${rm.name} (${rm.type} - ${rm.capacity} pl.)`;
                if (ev.room_id === rm.id) opt.selected = true;
                sel.appendChild(opt);
            });
            // onchange -> régénère le mail
            if (sel) sel.onchange = () => {
                const rid = sel.value;
                const name = sel.options[sel.selectedIndex] ? sel.options[sel.selectedIndex].text : rid;
                document.getElementById('room-mail-text').value = buildRoomMail(ev, rid, name);
            };
            document.getElementById('room-mail-text').value = buildRoomMail(ev, ev.room_id, ev.room_name);
            // Rend les suggestions cliquables pour choisir la salle (simplifie: on bind les boutons existants)
        }
        return r;
    };
}