/*
 * Politique de déplacement des cours (gestionnaire EDT).
 * Règle : il faut demander avant le JEUDI (à une heure limite) pour pouvoir déplacer
 * un cours de la semaine suivante. Au-delà du seuil, la semaine est "close" et les
 * créneaux de cette semaine ne sont plus proposés.
 */

let MOVE_POLICY = { dayLimit: 4, timeLimit: "18:00" };

// Applique la politique depuis l'objet constraints (mise à jour globale).
function applyMovePolicyFromConstraints() {
    if (typeof constraints !== 'undefined' && constraints && constraints.move_policy) {
        const p = constraints.move_policy;
        if (p.dayLimit) MOVE_POLICY.dayLimit = Number(p.dayLimit);
        if (p.timeLimit) MOVE_POLICY.timeLimit = p.timeLimit;
    }
}

// Charge les champs de la section Quotas depuis la politique courante.
function applyMovePolicyToForm() {
    const d = document.getElementById('move-policy-day');
    const t = document.getElementById('move-policy-time');
    if (d) d.value = MOVE_POLICY.dayLimit;
    if (t) t.value = MOVE_POLICY.timeLimit;
}

// Lit les champs de la section Quotas et les enregistre dans constraints.
function applyMovePolicyFromForm() {
    const d = document.getElementById('move-policy-day');
    const t = document.getElementById('move-policy-time');
    if (!constraints.move_policy) constraints.move_policy = {};
    if (d) constraints.move_policy.dayLimit = Number(d.value);
    if (t) constraints.move_policy.timeLimit = t.value;
    MOVE_POLICY.dayLimit = constraints.move_policy.dayLimit;
    MOVE_POLICY.timeLimit = constraints.move_policy.timeLimit;
}

// Règle : limite à respecter pour que la semaine cible soit déplaçable.
function policyNow() {
    return new Date();
}

function policyIsWeekOpen(targetWeek) {
    if (typeof getWeekDateRange !== 'function') return true;
    let r;
    try { r = getWeekDateRange(targetWeek); } catch (e) { return true; }
    const lundi = new Date(r.start);
    const limite = new Date(lundi);
    limite.setDate(limite.getDate() - (MOVE_POLICY.dayLimit || 4)); // jeudi précédent
    const [hh, mm] = (MOVE_POLICY.timeLimit || "18:00").split(":").map(Number);
    limite.setHours(hh || 18, mm || 0, 0, 0);
    if (targetWeek < 1 || targetWeek > 15) return false;
    return policyNow() < limite;
}

function policyOpenWeeks(baseWeek) {
    const open = [];
    for (let w = Math.max(1, baseWeek); w <= 15; w++) {
        if (policyIsWeekOpen(w)) open.push(w);
    }
    return open;
}

function policyMessage() {
    const days = ["", "Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"];
    const dayName = days[MOVE_POLICY.dayLimit] || 'Jeudi';
    return `Déplacement à demander avant le ${dayName} ${MOVE_POLICY.timeLimit} pour la semaine suivante.`;
}

// Exposer
window._policyIsWeekOpen = policyIsWeekOpen;
window._policyMessage = policyMessage;
window._policyOpenWeeks = policyOpenWeeks;
window._applyMovePolicyFromForm = applyMovePolicyFromForm;
window._applyMovePolicyFromConstraints = applyMovePolicyFromConstraints;
window._applyMovePolicyToForm = applyMovePolicyToForm;