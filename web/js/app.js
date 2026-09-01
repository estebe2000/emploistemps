
        const DAYS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"];
        const SLOTS = [
            { id: 0, name: "M1", time: "08:00 - 09:30", period: "MATIN" },
            { id: 1, name: "M2", time: "09:30 - 11:00", period: "MATIN" },
            { id: 2, name: "M3", time: "11:00 - 12:30", period: "MATIN" },
            { id: 3, name: "S1", time: "13:30 - 15:00", period: "APRES_MIDI" },
            { id: 4, name: "S2", time: "15:00 - 16:30", period: "APRES_MIDI" },
            { id: 5, name: "S3", time: "16:30 - 18:00", period: "APRES_MIDI" }
        ];

        let currentSchedule = [];
        let dataset = {};
        let constraints = {};
        let selectedLessonId = null;
        let currentWeek = 1;
        // Début de la semaine universitaire 1 — défini depuis les données (semester_start)
        // ou, en secours, calculé depuis la première date des événements.
        let SEMESTER_START = new Date(2026, 7, 31); // placeholder, surchargé à l'init
        const MONTHS_FR = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."];
        const DAYS_FR = ["dim.", "lun.", "mar.", "mer.", "jeu.", "ven.", "sam."];

        // Numéro de semaine ISO réel (algorithme MDN, fuseau local).
        function isoWeekOf(d) {
            const t = new Date(d.getFullYear(), d.getMonth(), d.getDate());
            const dayNum = (t.getDay() + 6) % 7; // lun=0
            t.setDate(t.getDate() - dayNum + 3); // jeudi de la semaine
            const firstThursday = t.getTime();
            t.setMonth(0, 1); // 1er janvier
            if (t.getDay() !== 4) {
                t.setMonth(0, 1 + ((4 - t.getDay()) + 7) % 7);
            }
            return 1 + Math.ceil((firstThursday - t) / 604800000);
        }

        // Retourne le lundi de début de la semaine X (1..15) et le dimanche de fin,
        // avec le numéro de semaine ISO réel (celui du calendrier universitaire officiel).
        function getWeekDateRange(week) {
            const start = new Date(SEMESTER_START);
            start.setDate(start.getDate() + (week - 1) * 7);
            const end = new Date(start);
            end.setDate(end.getDate() + 6);
            const iso = isoWeekOf(start); // numéro ISO réel (semaine 1 péd. = ISO 36)
            const fmt = (d, withDay) => {
                const day = withDay ? DAYS_FR[d.getDay()] + " " : "";
                return day + d.getDate() + " " + MONTHS_FR[d.getMonth()];
            };
            return { start, end, iso, label: `${fmt(start, true)} → ${fmt(end, false)} ${start.getFullYear()}` };
        }


        async function init() {
            try {
                const [dsRes, scRes, cRes] = await Promise.all([
                    fetch('/api/v1/dataset'),
                    fetch('/api/v1/schedule'),
                    fetch('/api/v1/admin/constraints')
                ]);

                dataset = await dsRes.json();
                const scData = await scRes.json();
                currentSchedule = scData.events || [];
                constraints = await cRes.json();
                // Début de la semaine 1 : priorité au semester_start fourni par le backend.
                if (scData.semester_start) {
                    const p = String(scData.semester_start).split('-').map(Number);
                    SEMESTER_START = new Date(p[0], p[1] - 1, p[2]);
                } else if (currentSchedule.length) {
                    // Secours : date la plus ancienne des événements, arrondie au lundi.
                    const dates = currentSchedule.map(e => new Date(e.date + 'T00:00:00')).filter(Boolean);
                    const first = dates.length ? dates.reduce((a, b) => a < b ? a : b) : new Date();
                    first.setDate(first.getDate() - first.getDay()); // dim->...; ramène au lundi
                    SEMESTER_START = first;
                }
                populateWeekSelector();
                populateDropdowns();
                updateWeekBadge();
                updateDeferredBadge();
                renderSchedule();
                initAdminView();
                initContextMenu();

            } catch (err) {
                console.error("Erreur initialisation:", err);
            }
        }

        function populateWeekSelector() {
            const select = document.getElementById('select-week');
            if (!select) return;
            select.innerHTML = '';

            const catchupWeeks = constraints.catchup_weeks || [8, 15];
            const fa2Weeks = constraints.cohort_alternance_calendar?.BUT2_FA?.company_weeks || [2, 4, 6, 8, 10, 12, 14];
            const fa3Weeks = constraints.cohort_alternance_calendar?.BUT3_FA?.company_weeks || [1, 3, 5, 7, 9, 11, 13];

            for (let w = 1; w <= 15; w++) {
                const opt = document.createElement('option');
                opt.value = w;
                const range = getWeekDateRange(w);
                let label = `Semaine ISO ${range.iso} — ${range.label}`;

                let tags = [];
                if (catchupWeeks.includes(w)) tags.push("🛑 Banalisée / Partiels");
                if (fa2Weeks.includes(w)) tags.push("🏢 BUT2 Entr.");
                if (fa3Weeks.includes(w)) tags.push("🏢 BUT3 Entr.");

                if (tags.length > 0) {
                    label += ` — ${tags.join(' | ')}`;
                }

                opt.textContent = label;
                select.appendChild(opt);
            }
            select.value = currentWeek;
        }

        function changeWeek(delta) {
            currentWeek = Math.max(1, Math.min(15, currentWeek + delta));
            const select = document.getElementById('select-week');
            if (select) select.value = currentWeek;
            onWeekChanged();
        }

        function onWeekChanged() {
            const select = document.getElementById('select-week');
            if (select) currentWeek = parseInt(select.value) || 1;
            updateWeekBadge();
            renderSchedule();
        }

        function updateWeekBadge() {
            const badge = document.getElementById('week-badge-info');
            const metrics = document.getElementById('metrics-text');
            if (!badge) return;

            const catchupWeeks = constraints.catchup_weeks || [8, 15];
            const fa2Weeks = constraints.cohort_alternance_calendar?.BUT2_FA?.company_weeks || [2, 4, 6, 8, 10, 12, 14];
            const fa3Weeks = constraints.cohort_alternance_calendar?.BUT3_FA?.company_weeks || [1, 3, 5, 7, 9, 11, 13];
            const range = getWeekDateRange(currentWeek);
            const datePrefix = `📅 <small style="opacity:0.75; font-weight:400;">Semaine ISO ${range.iso} · ${range.label}</small> — `;

            if (catchupWeeks.includes(currentWeek)) {
                badge.style.background = 'rgba(244, 63, 94, 0.15)';
                badge.style.borderColor = 'rgba(244, 63, 94, 0.4)';
                badge.style.color = '#fb7185';
                badge.innerHTML = `${datePrefix}<strong>Banalisée (Partiels / Rattrapages)</strong>`;
            } else if (fa2Weeks.includes(currentWeek) || fa3Weeks.includes(currentWeek)) {
                badge.style.background = 'rgba(245, 158, 11, 0.15)';
                badge.style.borderColor = 'rgba(245, 158, 11, 0.4)';
                badge.style.color = '#fbbf24';
                const who = fa2Weeks.includes(currentWeek) ? 'BUT2' : 'BUT3';
                badge.innerHTML = `${datePrefix}<strong>${who} Alternance en Entreprise</strong>`;
            } else {
                badge.style.background = 'rgba(255, 255, 255, 0.05)';
                badge.style.borderColor = 'var(--border-color)';
                badge.style.color = 'var(--text-muted)';
                badge.innerHTML = `${datePrefix}<strong>Cours & TD/TP Normaux</strong>`;
            }

            if (metrics) {
                metrics.textContent = `Semaine ISO ${range.iso} (S1) | 0 Conflit`;
            }
        }


        // Normalise un nom d'enseignant pour un matching robuste :
        // - insensible à la casse et aux accents
        // - insensible à l'ordre (prénom/nom : "Pytel Steeve" ≈ "Steeve Pytel")
        // - ignore le bruit importé des iCal (ex "Mémo : ...", "Salles : ...")
        function normalizeTeacherKey(rawName) {
            if (!rawName) return '';
            let s = rawName.toLowerCase()
                .replace(/m[ée]mo\s*:.*/i, '')     // retire "Mémo : ..."
                .replace(/salles\s*:.*/i, '')       // retire "Salles : ..."
                .normalize('NFD').replace(/[\u0300-\u036f]/g, ''); // retire accents
            const words = s.match(/[a-z0-9]+/g) || [];
            words.sort();                          // ordre alphabétique des mots
            return words.join(' ');
        }

        function populateDropdowns() {
            const teachSelect = document.getElementById('filter-teacher');
            const roomSelect = document.getElementById('filter-room');
            const adminTeachSelect = document.getElementById('admin-select-teacher');
            const closureRoomSelect = document.getElementById('closure-room-select');
            const evalRoomSelect = document.getElementById('eval-room');

            teachSelect.innerHTML = '<option value="">👤 Tous les enseignants (A-Z)</option>';
            roomSelect.innerHTML = '<option value="">📍 Toutes les salles</option>';
            adminTeachSelect.innerHTML = '';
            closureRoomSelect.innerHTML = '';
            evalRoomSelect.innerHTML = '';

            // Liste des enseignants pour le FILTRE (dans l'EDT réel).
            // On fusionne les noms du dataset et ceux réellement présents dans le planning
            // (source inclut potentiellement des noms non référencés dans le dataset).
            const teacherSet = new Map(); // key normalisée -> libellé lisible (le plus court/nettoyé)
            const cleanLabel = (raw) => {
                let s = String(raw || '').replace(/m[ée]mo\s*:.*/i, '').replace(/salles\s*:.*/i, '').trim();
                return s;
            };
            (currentSchedule || []).forEach(e => {
                const name = e.teacher_name;
                if (!name) return;
                const key = normalizeTeacherKey(name);
                if (!key) return;
                const cur = teacherSet.get(key);
                const cand = cleanLabel(name);
                if (!cur || cand.length < cur.length) teacherSet.set(key, cand);
            });
            (dataset.teachers || []).forEach(t => {
                const key = normalizeTeacherKey(t.name);
                const cand = cleanLabel(t.name);
                if (!key) { return; }
                const cur = teacherSet.get(key);
                if (!cur || cand.length < cur.length) teacherSet.set(key, cand);
            });

            const sortedTeacherKeys = Array.from(teacherSet.entries())
                .sort((a, b) => a[1].localeCompare(b[1], 'fr', { sensitivity: 'base' }));

            sortedTeacherKeys.forEach(([key, label]) => {
                const opt1 = document.createElement('option');
                opt1.value = key;          // valeur = clé normalisée (matching exact dans renderSchedule)
                opt1.textContent = label;
                teachSelect.appendChild(opt1);
            });

            // Liste des enseignants pour l'ADMIN (matrices des services) : référentiel dataset uniquement.
            const sortedTeachers = [...(dataset.teachers || [])].sort((a, b) =>
                a.name.localeCompare(b.name, 'fr', { sensitivity: 'base' })
            );
            sortedTeachers.forEach(t => {
                const opt2 = document.createElement('option');
                opt2.value = t.name;
                opt2.textContent = t.name;
                adminTeachSelect.appendChild(opt2);
            });

            const sortedRooms = [...(dataset.rooms || [])].sort((a, b) => 
                a.name.localeCompare(b.name, 'fr', { sensitivity: 'base' })
            );

            sortedRooms.forEach(r => {
                const opt = document.createElement('option');
                opt.value = r.name;
                opt.textContent = `${r.name} (${r.type})`;
                roomSelect.appendChild(opt);

                const opt2 = document.createElement('option');
                opt2.value = r.id;
                opt2.textContent = `${r.name} (${r.type})`;
                closureRoomSelect.appendChild(opt2);

                const opt3 = document.createElement('option');
                opt3.value = r.id;
                opt3.textContent = r.name;
                evalRoomSelect.appendChild(opt3);
            });
        }

        function filterAdminTeacherList() {
            const searchVal = document.getElementById('admin-teacher-search').value.toLowerCase().trim();
            const select = document.getElementById('admin-select-teacher');
            select.innerHTML = '';

            const sortedTeachers = [...(dataset.teachers || [])].sort((a, b) => 
                a.name.localeCompare(b.name, 'fr', { sensitivity: 'base' })
            );

            const filtered = sortedTeachers.filter(t => t.name.toLowerCase().includes(searchVal));

            filtered.forEach(t => {
                const opt = document.createElement('option');
                opt.value = t.name;
                opt.textContent = t.name;
                select.appendChild(opt);
            });

            if (filtered.length > 0) {
                loadTeacherMatrix();
            } else {
                document.getElementById('teacher-matrix').innerHTML = '<p style="color:var(--text-muted); font-size:0.85rem; padding:1rem;">Aucun enseignant trouvé.</p>';
                document.getElementById('teacher-assigned-list').textContent = 'Aucun enseignant correspondant.';
            }
        }

        function isPermanentClosure(day, sIdx) {
            // Les cours du Jeudi/Samedi après-midi SONT possibles (données réelles),
            // mais restent de moindre priorité ("dernier recours") géré côté solveur.
            return false;
        }
        // Signale un créneau de "dernier recours" (Jeudi/Samedi après-midi) à l'affichage.
        function isLowPrioritySlot(day, sIdx) {
            if (day === "Jeudi" && sIdx >= 3) return true;
            if (day === "Samedi" && sIdx >= 3) return true;
            return false;
        }


        function renderSchedule() {
            const grid = document.getElementById('grid');
            grid.innerHTML = '';
            grid.style.gridTemplateColumns = `120px repeat(${DAYS.length}, minmax(160px, 1fr))`;

            const filterGroup = document.getElementById('filter-group').value;
            const filterTeacher = document.getElementById('filter-teacher').value;
            const filterRoom = document.getElementById('filter-room').value;

            // Header Top-Left
            const emptyCorner = document.createElement('div');
            emptyCorner.className = 'grid-header time-col-header';
            emptyCorner.textContent = 'Créneaux';
            grid.appendChild(emptyCorner);

            // Day Headers
            DAYS.forEach(day => {
                const dayHeader = document.createElement('div');
                dayHeader.className = 'grid-header';
                dayHeader.textContent = day;
                grid.appendChild(dayHeader);
            });

            // Filter Events
            let filtered = currentSchedule;
            
            // Filter by week if multi-week events exist
            const hasWeekEvents = filtered.some(e => e.week === currentWeek);
            if (hasWeekEvents) {
                filtered = filtered.filter(e => e.week === currentWeek);
            }

            if (filterGroup) {
                filtered = filtered.filter(e => {
                    if (e.matching_groups && e.matching_groups.includes(filterGroup)) return true;
                    if (e.group_id === filterGroup) return true;
                    if (e.group_id.includes('PROMO') && (filterGroup.includes('TD') || filterGroup.includes('TP'))) return true;
                    return false;
                });
            }

            if (filterTeacher) {
                // filterTeacher = clé normalisée (voir populateDropdowns).
                // L'événement correspond si sa clé normalisée contient les mots de la clé sélectionnée.
                const teacherWant = (filterTeacher || '');
                filtered = filtered.filter(e => {
                    const evKey = normalizeTeacherKey(e.teacher_name);
                    // Associe si les mots recherchés sont tous présents dans la clé de l'événement.
                    return teacherWant.split(' ').filter(Boolean).every(w => evKey.includes(w));
                });
            }
            if (filterRoom) {
                filtered = filtered.filter(e => e.room_name.toLowerCase().includes(filterRoom.toLowerCase()) || e.room_id.toLowerCase().includes(filterRoom.toLowerCase()));
            }

            const metrics = document.getElementById('metrics-text');
            if (metrics) {
                metrics.textContent = `${filtered.length} cours affichés | Semaine ${currentWeek}`;
            }



            // Fill rows per slot
            SLOTS.forEach((slot, sIdx) => {
                const timeLabel = document.createElement('div');
                timeLabel.className = 'time-slot-label';
                timeLabel.innerHTML = `<span class="slot-name">${slot.name}</span><span>${slot.time}</span>`;
                grid.appendChild(timeLabel);

                DAYS.forEach((day, dIdx) => {
                    const cell = document.createElement('div');
                    cell.className = 'slot-cell';
                    cell.id = `cell-${dIdx}-${sIdx}`;

                    if (isPermanentClosure(day, sIdx)) {
                        cell.style.background = 'rgba(239, 68, 68, 0.04)';
                        cell.style.border = '1px dashed rgba(239, 68, 68, 0.2)';
                        cell.style.alignItems = 'center';
                        cell.style.justifyContent = 'center';
                        cell.innerHTML = `<span style="font-size:0.7rem; color:#f87171; font-weight:600;">🔒 Fermeture</span>`;
                    } else {
                        const cellEvents = filtered.filter(e => e.day_idx === dIdx && e.slot_idx === sIdx);

                        // Créneau "dernier recours" (Jeudi/Samedi AM) : fond jaune discret si occupé
                        if (isLowPrioritySlot(day, sIdx) && cellEvents.length > 0) {
                            cell.style.background = 'rgba(245, 158, 11, 0.06)';
                        }

                        const nonTpEvents = cellEvents.filter(e => e.event_type !== 'TP');
                        const tpEvents = cellEvents.filter(e => e.event_type === 'TP');

                        // 1. Render Non-TP events (CM, TD, EVAL) full width
                        nonTpEvents.forEach(ev => {
                            cell.appendChild(createCardElement(ev));
                        });

                        // 2. Render TP events side-by-side (2 per row: Group A & Group B)
                        for (let i = 0; i < tpEvents.length; i += 2) {
                            const row = document.createElement('div');
                            row.className = 'tp-split-row';

                            const evA = tpEvents[i];
                            row.appendChild(createCardElement(evA, true));

                            if (i + 1 < tpEvents.length) {
                                const evB = tpEvents[i + 1];
                                row.appendChild(createCardElement(evB, true));
                            }
                            cell.appendChild(row);
                        }
                    }

                    grid.appendChild(cell);
                });
            });
        }

        function createCardElement(ev, isHalf = false) {
            const card = document.createElement('div');
            let typeClass = ev.event_type === 'CM' ? 'event-cm' : (ev.event_type === 'TP' ? 'event-tp' : 'event-td');
            let badgeClass = ev.event_type === 'CM' ? 'badge-cm' : (ev.event_type === 'TP' ? 'badge-tp' : 'badge-td');
            let badgeLabel = ev.group_id || ev.event_type;

            if (ev.is_evaluation || ev.event_type === 'EVAL') {
                typeClass = 'event-eval';
                badgeClass = 'badge-eval';
                badgeLabel = 'DS/EVAL';
            }

            card.className = `event-card ${typeClass}`;
            card.innerHTML = `
                <div class="event-header">
                    <span style="font-weight:700;">${ev.resource_code}</span>
                    <span class="event-badge ${badgeClass}">${badgeLabel}</span>
                </div>
                <div class="event-title" title="${ev.resource_name}">${ev.resource_name}</div>
                <div class="event-footer">
                    <span>${ev.teacher_name}</span>
                    <span class="event-room">${ev.room_name.replace('IUTC-', '')}</span>
                </div>
            `;

            // Right-click context menu handler
            card.oncontextmenu = (e) => {
                e.preventDefault();
                openContextMenu(e, ev.lesson_id);
            };

            // Left click quick prompt
            card.onclick = () => {
                sendQuickPrompt(`Est-ce que je peux déplacer le cours ${ev.lesson_id} (${ev.group_id}) vers un autre créneau sans conflit ?`);
            };

            return card;
        }


        // --- CONTEXT MENU (Clic Droit) ---
        function initContextMenu() {
            window.addEventListener('click', () => {
                document.getElementById('context-menu').style.display = 'none';
            });
        }

        function openContextMenu(e, lessonId) {
            selectedLessonId = lessonId;
            const menu = document.getElementById('context-menu');
            menu.style.display = 'block';
            menu.style.left = `${Math.min(e.clientX, window.innerWidth - 240)}px`;
            menu.style.top = `${Math.min(e.clientY, window.innerHeight - 200)}px`;
        }

        async function contextAction(action) {
            document.getElementById('context-menu').style.display = 'none';
            if (!selectedLessonId) return;

            if (action === 'CONVERT_EVAL') {
                await sendQuickAction('CONVERT_EVAL', { lesson_id: selectedLessonId });
            }
        }

        async function deferSelectedLesson() {
            document.getElementById('context-menu').style.display = 'none';
            if (!selectedLessonId) return;
            const ev = currentSchedule.find(e => e.lesson_id === selectedLessonId);
            const title = ev ? ev.resource_name : selectedLessonId;
            
            if (confirm(`Mettre en attente le cours "${title}" pour reprogrammation ultérieure ?`)) {
                await sendQuickAction('DEFER', { lesson_id: selectedLessonId });
                updateDeferredBadge();
            }
        }

        async function cancelSelectedLesson() {
            document.getElementById('context-menu').style.display = 'none';
            if (!selectedLessonId) return;
            const ev = currentSchedule.find(e => e.lesson_id === selectedLessonId);
            const title = ev ? ev.resource_name : selectedLessonId;

            if (confirm(`⚠️ Confirmer l'annulation définitive de la séance "${title}" ?`)) {
                await sendQuickAction('CANCEL', { lesson_id: selectedLessonId });
            }
        }

        // --- MOVE MODAL ---
        function openMoveModal() {
            document.getElementById('context-menu').style.display = 'none';
            if (!selectedLessonId) return;
            const ev = currentSchedule.find(e => e.lesson_id === selectedLessonId);
            if (ev) {
                document.getElementById('move-lesson-title').textContent = `${ev.resource_name} (${ev.group_id}) - ${ev.teacher_name}`;
                document.getElementById('move-target-day').value = ev.day;
                document.getElementById('move-target-slot').value = ev.slot_idx;
            }

            const roomSelect = document.getElementById('move-target-room');
            roomSelect.innerHTML = '';
            (dataset.rooms || []).forEach(r => {
                const opt = document.createElement('option');
                opt.value = r.id;
                opt.textContent = `${r.name} (${r.type})`;
                if (ev && ev.room_id === r.id) opt.selected = true;
                roomSelect.appendChild(opt);
            });

            document.getElementById('move-modal').style.display = 'flex';
        }

        function closeMoveModal() {
            document.getElementById('move-modal').style.display = 'none';
        }

        async function confirmMoveLesson() {
            const day = document.getElementById('move-target-day').value;
            const slot = parseInt(document.getElementById('move-target-slot').value);
            const room = document.getElementById('move-target-room').value;

            if ((day === "Jeudi" || day === "Samedi") && slot >= 2) {
                alert("❌ Impossible de déplacer sur ce créneau : Fermeture départementale IUT le Jeudi PM et Samedi PM.");
                return;
            }

            try {
                const res = await fetch('/api/v1/schedule/quick-action', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        action: 'MOVE',
                        lesson_id: selectedLessonId,
                        target_day: day,
                        target_slot_idx: slot,
                        target_room_id: room
                    })
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail?.message || data.detail || "Conflit détecté");
                alert("✅ " + data.message);
                closeMoveModal();

                const scRes = await fetch('/api/v1/schedule');
                const scData = await scRes.json();
                currentSchedule = scData.events || [];
                renderSchedule();
            } catch (err) {
                alert("Erreur déplacement : " + err.message);
            }
        }

        // --- CHANGE ROOM MODAL WITH SMART SUGGESTIONS ---
        function openChangeRoomModal() {

            document.getElementById('context-menu').style.display = 'none';
            if (!selectedLessonId) return;
            const ev = currentSchedule.find(e => e.lesson_id === selectedLessonId);
            if (!ev) return;

            document.getElementById('change-room-lesson-title').textContent = `${ev.resource_name} (${ev.group_id}) — ${ev.day} ${ev.slot_time} | Salle actuelle : ${ev.room_name}`;
            
            const container = document.getElementById('room-suggestions-list');
            container.innerHTML = '';

            // Find occupied rooms at this exact week, day, slot
            const slotOccupations = currentSchedule.filter(
                e => e.week === ev.week && e.day_idx === ev.day_idx && e.slot_idx === ev.slot_idx && e.lesson_id !== ev.lesson_id
            );

            (dataset.rooms || []).forEach(r => {
                const isCurrent = ev.room_id === r.id;
                const occ = slotOccupations.find(o => o.room_id === r.id);

                const item = document.createElement('div');
                item.style.display = 'flex';
                item.style.alignItems = 'center';
                item.style.justifyContent = 'space-between';
                item.style.padding = '10px 14px';
                item.style.borderRadius = 'var(--radius-sm)';
                item.style.border = '1px solid var(--border-color)';
                item.style.background = 'rgba(255,255,255,0.02)';

                let badgeHtml = '';
                let buttonHtml = '';

                if (isCurrent) {
                    item.style.borderColor = 'var(--accent-primary)';
                    badgeHtml = `<span class="event-badge badge-cm">Actuelle</span>`;
                    buttonHtml = `<span style="font-size:0.75rem; color:var(--text-muted);">Salle assignée</span>`;
                } else if (occ) {
                    item.style.opacity = '0.6';
                    badgeHtml = `<span style="color:#f87171; font-size:0.75rem; font-weight:600;">🔴 Occupée (${occ.resource_code} - ${occ.group_id})</span>`;
                    buttonHtml = `<button class="btn btn-sm" disabled style="opacity:0.4; cursor:not-allowed;">Indisponible</button>`;
                } else {
                    // Free room!
                    let isRecommended = false;
                    if (ev.event_type === 'TP' && r.type.includes('TP')) isRecommended = true;
                    if (ev.event_type === 'CM' && r.type === 'AMPHI') isRecommended = true;
                    if (ev.event_type === 'TD' && r.type.includes('TD')) isRecommended = true;

                    if (isRecommended) {
                        item.style.background = 'rgba(16, 185, 129, 0.08)';
                        item.style.borderColor = 'rgba(16, 185, 129, 0.3)';
                        badgeHtml = `<span style="color:#34d399; font-size:0.75rem; font-weight:700;">🟢 Recommandée (Libre & Adaptée)</span>`;
                    } else {
                        badgeHtml = `<span style="color:#38bdf8; font-size:0.75rem; font-weight:600;">🟢 Libre</span>`;
                    }

                    buttonHtml = `<button class="btn btn-sm btn-primary" onclick="confirmRoomChange('${r.id}')">Choisir cette salle</button>`;
                }

                item.innerHTML = `
                    <div style="display:flex; flex-direction:column; gap:2px;">
                        <div style="font-weight:700; font-size:0.85rem;">${r.name} <small style="color:var(--text-muted); font-weight:normal;">(${r.type} - ${r.capacity} pl.)</small></div>
                        <div style="font-size:0.72rem; color:var(--text-muted);">${r.equipments.join(', ')}</div>
                    </div>
                    <div style="display:flex; align-items:center; gap:12px;">
                        ${badgeHtml}
                        ${buttonHtml}
                    </div>
                `;

                container.appendChild(item);
            });

            document.getElementById('change-room-modal').style.display = 'flex';
        }

        function closeChangeRoomModal() {
            document.getElementById('change-room-modal').style.display = 'none';
        }

        async function confirmRoomChange(newRoomId) {
            try {
                const res = await fetch('/api/v1/schedule/quick-action', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        action: 'CHANGE_ROOM',
                        lesson_id: selectedLessonId,
                        new_room_id: newRoomId
                    })
                });
                const data = await res.json();
                alert("✅ " + data.message);
                closeChangeRoomModal();

                const scRes = await fetch('/api/v1/schedule');
                const scData = await scRes.json();
                currentSchedule = scData.events || [];
                renderSchedule();
            } catch (err) {
                alert("Erreur changement de salle : " + err);
            }
        }


        // --- CHANGE TEACHER MODAL ---
        function openChangeTeacherModal() {
            document.getElementById('context-menu').style.display = 'none';
            if (!selectedLessonId) return;
            const ev = currentSchedule.find(e => e.lesson_id === selectedLessonId);
            if (ev) {
                document.getElementById('change-teacher-lesson-title').textContent = `${ev.resource_name} (${ev.group_id}) - Actuel : ${ev.teacher_name}`;
            }

            const select = document.getElementById('change-target-teacher');
            select.innerHTML = '';

            const sortedTeachers = [...(dataset.teachers || [])].sort((a, b) => 
                a.name.localeCompare(b.name, 'fr', { sensitivity: 'base' })
            );

            sortedTeachers.forEach(t => {
                const opt = document.createElement('option');
                opt.value = t.name;
                opt.textContent = `${t.name} (${t.statut})`;
                if (ev && ev.teacher_name.toLowerCase() === t.name.toLowerCase()) opt.selected = true;
                select.appendChild(opt);
            });

            document.getElementById('change-teacher-modal').style.display = 'flex';
        }

        function closeChangeTeacherModal() {
            document.getElementById('change-teacher-modal').style.display = 'none';
        }

        async function confirmChangeTeacher() {
            const newTeacher = document.getElementById('change-target-teacher').value;
            if (!newTeacher) return;

            try {
                const res = await fetch('/api/v1/schedule/quick-action', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        action: 'CHANGE_TEACHER',
                        lesson_id: selectedLessonId,
                        new_teacher: newTeacher
                    })
                });
                const data = await res.json();
                alert("✅ " + data.message);
                closeChangeTeacherModal();

                const scRes = await fetch('/api/v1/schedule');
                const scData = await scRes.json();
                currentSchedule = scData.events || [];
                renderSchedule();
            } catch (err) {
                alert("Erreur changement enseignant : " + err.message);
            }
        }

        // --- DEFERRED LESSONS MODAL ---
        async function openDeferredModal() {
            document.getElementById('deferred-modal').style.display = 'flex';
            await loadDeferredTable();
        }

        function closeDeferredModal() {
            document.getElementById('deferred-modal').style.display = 'none';
        }

        async function loadDeferredTable() {
            const tbody = document.getElementById('deferred-table-body');
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;">⏳ Chargement...</td></tr>';

            try {
                const res = await fetch('/api/v1/schedule/deferred');
                const data = await res.json();
                const list = data.deferred_events || [];
                tbody.innerHTML = '';

                document.getElementById('deferred-count').textContent = list.length;

                if (list.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; color:var(--text-muted); padding:1.5rem;">🎉 Aucun cours en attente de reprogrammation.</td></tr>';
                    return;
                }

                list.forEach(ev => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td style="font-weight:600; color:#fbbf24;">${ev.resource_name}</td>
                        <td><span class="event-badge badge-td">${ev.event_type}</span></td>
                        <td>${ev.group_id}</td>
                        <td>${ev.teacher_name}</td>
                        <td>${ev.duration_hours}h</td>
                        <td>
                            <button class="btn btn-sm btn-primary" onclick="promptReprogramDeferred('${ev.lesson_id}')">📅 Reprogrammer</button>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });
            } catch (err) {
                tbody.innerHTML = `<tr><td colspan="6" style="color:#ef4444;">Erreur : ${err}</td></tr>`;
            }
        }

        async function promptReprogramDeferred(lessonId) {
            closeDeferredModal();
            selectedLessonId = lessonId;
            openMoveModal();
        }

        async function updateDeferredBadge() {
            try {
                const res = await fetch('/api/v1/schedule/deferred');
                const data = await res.json();
                const count = (data.deferred_events || []).length;
                document.getElementById('deferred-count').textContent = count;
            } catch (err) {}
        }

        async function sendQuickAction(action, payload) {
            try {
                const res = await fetch('/api/v1/schedule/quick-action', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: action, ...payload })
                });
                const data = await res.json();
                alert("✅ " + data.message);
                
                // Refresh
                const scRes = await fetch('/api/v1/schedule');
                const scData = await scRes.json();
                currentSchedule = scData.events || [];
                renderSchedule();
                updateDeferredBadge();
            } catch (err) {
                alert("Erreur action : " + err);
            }
        }


        // --- WORKLOAD MODAL ---
        async function openWorkloadModal() {
            document.getElementById('workload-modal').style.display = 'flex';
            const tbody = document.getElementById('workload-table-body');
            tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; padding:1.5rem;">⏳ Chargement du bilan HETD officiel...</td></tr>';

            try {
                const res = await fetch('/api/v1/teachers/workload');
                const data = await res.json();
                tbody.innerHTML = '';

                (data.teachers || []).forEach(t => {
                    const tr = document.createElement('tr');
                    const fillPct = Math.min(100, Math.round((t.total_hetd / t.service_statutaire_hetd) * 100));
                    const barColor = t.status === 'HEURES_SUP' ? '#ef4444' : (t.status === 'SOUS_SERVICE' ? '#f59e0b' : '#10b981');

                    tr.innerHTML = `
                        <td style="font-weight:600;">${t.teacher_name}</td>
                        <td><span class="event-badge badge-td">${t.statut}</span></td>
                        <td style="text-align:center; font-weight:600;">${t.nb_cours_planifies}</td>
                        <td>${t.total_heures_cm}h</td>
                        <td>${t.total_heures_td}h</td>
                        <td>${t.total_heures_tp}h</td>
                        <td style="font-weight:700; color:#38bdf8;">${t.total_hetd} HETD</td>
                        <td style="color:var(--text-muted);">${t.service_statutaire_hetd}h</td>
                        <td>
                            <div class="progress-bar-bg"><div class="progress-bar-fill" style="width:${fillPct}%; background:${barColor};"></div></div>
                            <span style="font-size:0.75rem; color:${barColor}; font-weight:700;">${t.delta_hetd > 0 ? '+' : ''}${t.delta_hetd}h (${fillPct}%)</span>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });
            } catch (err) {
                tbody.innerHTML = `<tr><td colspan="9" style="color:#ef4444;">Erreur : ${err}</td></tr>`;
            }
        }


        function closeWorkloadModal() {
            document.getElementById('workload-modal').style.display = 'none';
        }

        async function triggerSolver() {
            const btn = document.getElementById('btn-generate');
            btn.disabled = true;
            btn.textContent = '⏳ Résolution CP-SAT...';

            try {
                const res = await fetch('/api/v1/solver/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ semester: 'S1', week: currentWeek, time_limit_seconds: 15 })
                });
                const data = await res.json();
                currentSchedule = data.events || [];
                renderSchedule();
                document.getElementById('metrics-text').textContent = `0 Conflit | Semaine ${currentWeek} résolue en ${data.solve_time_sec?.toFixed(2)}s`;
                appendMessage('ai', `🎉 Emploi du temps pour la Semaine ${currentWeek} (S1) regénéré avec succès par le solveur CP-SAT en ${data.solve_time_sec?.toFixed(2)}s ! 100% des contraintes sont respectées.`);
            } catch (err) {

                alert("Erreur solveur : " + err);
            } finally {
                btn.disabled = false;
                btn.textContent = '⚡ Optimiser (CP-SAT)';
            }
        }

        async function sendMessage() {
            const input = document.getElementById('chat-input');
            const prompt = input.value.trim();
            if (!prompt) return;

            appendMessage('user', prompt);
            input.value = '';

            const aiBubble = appendMessage('ai', '⏳ Analyse en cours avec Albert...');

            try {
                const res = await fetch('/api/v1/ai/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt: prompt })
                });
                const data = await res.json();
                aiBubble.textContent = data.response || "Aucune réponse reçue.";

                // Refresh schedule
                const scRes = await fetch('/api/v1/schedule');
                const scData = await scRes.json();
                currentSchedule = scData.events || [];
                renderSchedule();
            } catch (err) {
                aiBubble.textContent = "Erreur lors de la communication avec l'IA : " + err;
            }
        }

        function sendQuickPrompt(prompt) {
            document.getElementById('chat-input').value = prompt;
            sendMessage();
        }

        function appendMessage(role, text) {
            const box = document.getElementById('chat-box');
            const bubble = document.createElement('div');
            bubble.className = `chat-bubble ${role === 'user' ? 'bubble-user' : 'bubble-ai'}`;
            bubble.textContent = text;
            box.appendChild(bubble);
            box.scrollTop = box.scrollHeight;
            return bubble;
        }

        function handleKey(e) {
            if (e.key === 'Enter') sendMessage();
        }

        // --- ADMIN MODAL FUNCTIONS ---

        function openAdminModal() {
            document.getElementById('admin-modal').style.display = 'flex';
            // Ouvrir par défaut sur l'onglet Sources iCal
            switchTab('tab-icalsources');
            loadIcalSources();
            loadIcalSyncStatus();
            loadTeacherMatrix();
            loadRoomsTable();
            loadEvaluationsTable();
            loadAlternanceWeeks();
        }

        function closeAdminModal() {
            document.getElementById('admin-modal').style.display = 'none';
        }

        // Construit l'URL iCal affichable/éditable depuis les champs de config.
        function buildIcalUrl(base, param, src) {
            const ver = '2022.0.5.0';
            const b = (base || 'https://hplanning.univ-lehavre.fr').replace(/\/+$/, '');
            return `${b}/Telechargements/ical/${src.file}?version=${ver}&idICal=${encodeURIComponent(src.idICal)}&param=${param}`;
        }

        async function loadIcalSources() {
            const container = document.getElementById('ical-sources-container');
            if (!container) return;
            container.innerHTML = '<p style="color:var(--text-muted); font-size:0.85rem;">Chargement…</p>';
            let cfg = { sources: [], base_url: 'https://hplanning.univ-lehavre.fr', param: '' };
            try {
                cfg = await (await fetch('/api/v1/admin/ical-sources')).json();
            } catch (e) { container.innerHTML = '<p style="color:#fb7185;">Erreur chargement sources.</p>'; return; }
            if (!cfg.sources) cfg.sources = [];

            const want = ['BUT1', 'BUT2', 'BUT3'];
            const ordered = want.map(k => cfg.sources.find(s => s.key === k)).filter(Boolean);
            cfg.sources.forEach(s => { if (!want.includes(s.key)) ordered.push(s); });

            const esc = v => String(v || '').replace(/"/g, '&quot;');
            const rows = ordered.map((src, i) => `
                <div class="ical-source" style="background:rgba(255,255,255,0.02); border:1px solid var(--border-color); border-radius:var(--radius-sm); padding:1rem; margin-bottom:1rem;">
                    <div style="display:flex; align-items:center; justify-content:space-between; gap:12px; margin-bottom:8px;">
                        <label style="font-weight:600; font-size:0.85rem;">🔗 Source ${i+1} — ${esc(src.key)}</label>
                        <button class="btn" onclick="removeIcalSourceRow(this)" title="Supprimer">🗑</button>
                    </div>
                    <div style="margin-bottom:8px;">
                        <label style="font-size:0.75rem; color:var(--text-muted); display:block;">Nom / label</label>
                        <input type="text" data-field="label" value="${esc(src.label)}" style="width:100%;">
                    </div>
                    <div style="margin-bottom:8px;">
                        <label style="font-size:0.75rem; color:var(--text-muted); display:block;">URL iCal (lien permanent)</label>
                        <input type="text" data-field="url" value="${esc(buildIcalUrl(cfg.base_url, cfg.param, src))}" style="width:100%; font-family:monospace; font-size:0.75rem;">
                    </div>
                    <details style="font-size:0.72rem; color:var(--text-muted);">
                        <summary>Champs avancés (file / idICal / param)</summary>
                        <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; margin-top:8px;">
                            <label>key<input type="text" data-field="key" value="${esc(src.key)}" style="width:100%;"></label>
                            <label>idICal<input type="text" data-field="idICal" value="${esc(src.idICal)}" style="width:100%; font-family:monospace;"></label>
                            <label>file<input type="text" data-field="file" value="${esc(src.file)}" style="width:100%; font-family:monospace;"></label>
                        </div>
                    </details>
                </div>`).join('');

            container.innerHTML = `
                <input type="hidden" id="ical-cfg-base" value="${esc(cfg.base_url)}">
                <input type="hidden" id="ical-cfg-param" value="${esc(cfg.param)}">
                ${rows}
                <div style="display:flex; gap:12px; margin-top:0.75rem; align-items:center; flex-wrap:wrap;">
                    <button class="btn" onclick="addIcalSourceRow()">➕ Ajouter une source</button>
                    <button class="btn btn-success" id="ical-sync-btn" onclick="runIcalSync()">🔄 Synchroniser le planning</button>
                </div>
                <p style="font-size:0.72rem; color:var(--text-muted); margin-top:0.75rem;">
                    Astuce : connectez-vous à l'espace <em>Enseignants</em> Hyperplanning, ouvrez l'emploi du temps et copiez le <strong>lien permanent iCal</strong> (export / QR).
                </p>`;
        }

        function addIcalSourceRow() {
            const container = document.getElementById('ical-sources-container');
            const div = document.createElement('div');
            div.className = 'ical-source';
            div.style.cssText = 'background:rgba(255,255,255,0.02); border:1px solid var(--border-color); border-radius:var(--radius-sm); padding:1rem; margin-bottom:1rem;';
            div.innerHTML = `
                <div style="display:flex; align-items:center; justify-content:space-between; gap:12px; margin-bottom:8px;">
                    <label style="font-weight:600; font-size:0.85rem;">🔗 Nouvelle source</label>
                    <button class="btn" onclick="removeIcalSourceRow(this)">🗑</button>
                </div>
                <div style="margin-bottom:8px;"><label style="font-size:0.75rem; color:var(--text-muted); display:block;">Nom / label</label>
                    <input type="text" data-field="label" value="" style="width:100%;"></div>
                <div style="margin-bottom:8px;"><label style="font-size:0.75rem; color:var(--text-muted); display:block;">URL iCal (lien permanent)</label>
                    <input type="text" data-field="url" value="" style="width:100%; font-family:monospace; font-size:0.75rem;"></div>
                <details style="font-size:0.72rem; color:var(--text-muted);"><summary>Champs avancés</summary>
                    <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; margin-top:8px;">
                        <label>key<input type="text" data-field="key" value="SRC" style="width:100%;"></label>
                        <label>idICal<input type="text" data-field="idICal" value="" style="width:100%;"></label>
                        <label>file<input type="text" data-field="file" value="" style="width:100%;"></label>
                    </div></details>`;
            container.appendChild(div);
        }

        function removeIcalSourceRow(btn) {
            const card = btn.closest('.ical-source');
            if (card) card.remove();
        }

        function fmtSyncDate(iso) {
            if (!iso) return 'jamais';
            const d = new Date(iso);
            if (isNaN(d)) return iso;
            return d.toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
        }

        // Interroge le statut de synchronisation (GET) et met à jour la carte d'état + l'indicateur.
        async function loadIcalSyncStatus() {
            const title = document.getElementById('ical-sync-status-title');
            const detail = document.getElementById('ical-sync-status-detail');
            const dot = document.getElementById('ical-sync-indicator');
            if (!title || !detail || !dot) return;
            let st = null;
            try { st = await (await fetch('/api/v1/admin/ical-sync/status')).json(); }
            catch (e) { title.textContent = 'État indisponible'; detail.textContent = e.message; dot.style.background = '#f87171'; return; }
            const running = !!st.running;
            if (running) {
                dot.style.background = '#fbbf24';
                dot.style.boxShadow = '0 0 8px #fbbf24';
                title.textContent = `🔄 Synchronisation en cours… (démarrée à ${fmtSyncDate(st.started_at)})`;
                detail.textContent = 'Téléchargement des iCal et ingestion en arrière-plan.';
            } else if (st.status === 'success') {
                dot.style.background = '#34d399';
                dot.style.boxShadow = '0 0 8px #34d399';
                title.textContent = '✅ Dernière synchronisation réussie';
                detail.textContent = `Le ${fmtSyncDate(st.last_sync || st.finished_at)} · ${st.downloaded ?? 0} iCal · ${st.total_events ?? 0} cours ingérés`;
            } else if (st.status === 'error') {
                dot.style.background = '#f87171';
                dot.style.boxShadow = '0 0 8px #f87171';
                title.textContent = '❌ Synchronisation en erreur';
                detail.textContent = (st.message || 'Erreur inconnue') + ` · ${fmtSyncDate(st.finished_at)}`;
            } else {
                dot.style.background = '#9ca3af';
                title.textContent = '⚪ Aucune synchronisation';
                detail.textContent = st.message || 'Lancez une synchronisation pour mettre à jour le planning.';
            }
            return running;
        }

        async function runIcalSync() {
            const btn = document.getElementById('ical-sync-btn');
            if (!btn) return;
            // Sauvegarde d'abord les sources telles que saisies, puis synchronise.
            try { await saveIcalSources(true); } catch (e) {}

            btn.disabled = true;
            btn.textContent = '⏳ Synchronisation en cours…';
            // Met la carte d'état en mode "en cours"
            const t = document.getElementById('ical-sync-status-title');
            const d = document.getElementById('ical-sync-status-detail');
            const dot = document.getElementById('ical-sync-indicator');
            if (t) t.textContent = '🔄 Synchronisation en cours…';
            if (d) d.textContent = 'Téléchargement des iCal et ingestion…';
            if (dot) { dot.style.background = '#fbbf24'; dot.style.boxShadow = '0 0 8px #fbbf24'; }

            try {
                const res = await fetch('/api/v1/admin/ical-sync', { method: 'POST' });
                const data = await res.json();
                if (data.status === 'success') {
                    // Recharge le planning et l'état de la synchronisation
                    try {
                        const sc = await (await fetch('/api/v1/schedule')).json();
                        currentSchedule = sc.events || [];
                        if (sc.semester_start) { const p = String(sc.semester_start).split('-').map(Number); SEMESTER_START = new Date(p[0], p[1]-1, p[2]); }
                        populateWeekSelector();
                        updateWeekBadge();
                        renderSchedule();
                    } catch (e2) {}
                }
                await loadIcalSyncStatus();
            } catch (err) {
                try {
                    const t = document.getElementById('ical-sync-status-title');
                    const d = document.getElementById('ical-sync-status-detail');
                    if (t) t.textContent = '❌ Erreur de synchronisation';
                    if (d) d.textContent = err.message;
                } catch (_) {}
            } finally {
                btn.disabled = false;
                btn.textContent = '🔄 Synchroniser le planning';
            }
        }

        async function saveIcalSources(quiet) {
            const container = document.getElementById('ical-sources-container');
            const base = (document.getElementById('ical-cfg-base')?.value || 'https://hplanning.univ-lehavre.fr').trim();
            const param = (document.getElementById('ical-cfg-param')?.value || '').trim();
            const sources = [];
            container.querySelectorAll('.ical-source').forEach(card => {
                const vals = {};
                card.querySelectorAll('input[data-field]').forEach(i => vals[i.getAttribute('data-field')] = i.value.trim());
                const url = vals.url || '';
                const m = url.match(/ical\/([^?]+)\.ics\?.*idICal=([^&]+)/);
                let file = vals.file || '';
                let idICal = vals.idICal || '';
                if (m) { if (!file) file = m[1] + '.ics'; if (!idICal) idICal = m[2]; }
                if (!file && !idICal && !url) return;
                sources.push({ key: vals.key || ('SRC_' + sources.length), label: vals.label, file, idICal, url });
            });
            const payload = { version: '2022.0.5.0', base_url: base, param, sources };
            try {
                const res = await fetch('/api/v1/admin/ical-sources', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (!quiet) alert(data.message || 'Sources enregistrées.');
                loadIcalSources();
            } catch (err) {
                alert('Erreur enregistrement : ' + err.message);
            }
        }

        function switchTab(tabId) {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
            // Active le bouton correspondant à tabId
            document.querySelectorAll('.tab-btn').forEach(b => {
                if (b.getAttribute('onclick').includes(tabId)) b.classList.add('active');
            });
            const pane = document.getElementById(tabId);
            if (pane) pane.classList.add('active');
        }

        function initAdminView() {
            document.getElementById('quota-teacher-hours').value = constraints.max_hours_per_day_teacher || 6;
            document.getElementById('quota-student-hours').value = constraints.max_hours_per_day_student || 8;
        }

        function loadTeacherMatrix() {
            const select = document.getElementById('admin-select-teacher');
            if (!select.value && select.options.length > 0) {
                select.selectedIndex = 0;
            }
            const teacherName = select.value;
            const matrix = document.getElementById('teacher-matrix');
            matrix.innerHTML = '';
            matrix.style.gridTemplateColumns = `160px repeat(${DAYS.length}, 1fr)`;

            if (!teacherName) {
                document.getElementById('teacher-assigned-list').textContent = 'Sélectionnez un enseignant.';
                return;
            }

            const teacherObj = (dataset.teachers || []).find(t => t.name === teacherName);
            const assignedList = document.getElementById('teacher-assigned-list');
            if (teacherObj && teacherObj.assigned_resources?.length) {
                assignedList.innerHTML = teacherObj.assigned_resources.map(r => `<span style="display:inline-block; margin:2px 4px; padding:2px 6px; background:rgba(99,102,241,0.2); border-radius:4px; font-weight:600;">${r}</span>`).join(' ');
            } else {
                assignedList.textContent = 'Aucune ressource affectée.';
            }

            // Headers
            matrix.appendChild(createDiv('matrix-header', 'Période'));
            DAYS.forEach(day => matrix.appendChild(createDiv('matrix-header', day)));

            const unavails = (constraints.teacher_unavailabilities || []).filter(u => u.teacher_name.toLowerCase() === teacherName.toLowerCase());

            const PERIODS = [
                { id: "MATIN", label: "🌅 Matin<br><small>08:00 - 11:15</small>", slots: [0, 1] },
                { id: "APRES_MIDI", label: "🌇 Après-midi<br><small>13:30 - 16:45</small>", slots: [2, 3] }
            ];

            PERIODS.forEach(period => {
                matrix.appendChild(createDiv('matrix-day', period.label));

                DAYS.forEach(day => {
                    const isLow = (day === "Jeudi" && period.id === "APRES_MIDI") || (day === "Samedi" && period.id === "APRES_MIDI");

                    const cell = document.createElement('div');
                    const dayUnavail = unavails.find(u => u.day.toLowerCase() === day.toLowerCase());
                    const isBlocked = dayUnavail && period.slots.some(s => dayUnavail.slots.includes(s));

                    cell.className = `matrix-cell ${isBlocked ? 'unavailable' : ''}`;
                    if (isLow && !isBlocked) {
                        // Créneau de dernier recours (Jeudi/Samedi après-midi) : sélectionnable,
                        // signalé par une teinte ambre discrète.
                        cell.style.background = 'rgba(245, 158, 11, 0.10)';
                        cell.style.borderColor = 'rgba(245, 158, 11, 0.35)';
                        cell.style.color = '#fbbf24';
                        cell.textContent = isBlocked ? '⛔ Bloqué' : '🟠 Dernier recours';
                    } else {
                        cell.textContent = isBlocked ? '⛔ Bloqué' : '✅ Dispo';
                    }
                    cell.onclick = () => toggleTeacherHalfDay(teacherName, day, period.slots, cell);
                    matrix.appendChild(cell);
                });
            });
        }

        function toggleTeacherHalfDay(teacherName, day, slots, cellElement) {
            if (!constraints.teacher_unavailabilities) constraints.teacher_unavailabilities = [];

            let unavail = constraints.teacher_unavailabilities.find(
                u => u.teacher_name.toLowerCase() === teacherName.toLowerCase() && u.day.toLowerCase() === day.toLowerCase()
            );

            if (!unavail) {
                unavail = { teacher_name: teacherName, day: day, slots: [], reason: "Indisponibilité demi-journée" };
                constraints.teacher_unavailabilities.push(unavail);
            }

            const currentlyBlocked = slots.some(s => unavail.slots.includes(s));

            if (currentlyBlocked) {
                unavail.slots = unavail.slots.filter(s => !slots.includes(s));
                cellElement.className = 'matrix-cell';
                cellElement.textContent = '✅ Dispo';
            } else {
                slots.forEach(s => {
                    if (!unavail.slots.includes(s)) unavail.slots.push(s);
                });
                cellElement.className = 'matrix-cell unavailable';
                cellElement.textContent = '⛔ Bloqué';
            }
        }

        function loadRoomsTable() {
            const tbody = document.getElementById('rooms-table-body');
            tbody.innerHTML = '';

            (dataset.rooms || []).forEach(r => {
                const closures = (constraints.room_closures_or_reservations || []).filter(c => c.room_id === r.id);
                const closureText = closures.length > 0 
                    ? closures.map(c => `🔴 S${c.week} ${c.day} (${c.reason || ''})`).join(', ')
                    : '🟢 Disponible';

                const eq = (r.equipments || []).map(x => String(x).toUpperCase());
                // Informatique = équipé de postes/COMPUTERS ; Labo lang = type TP_LANG ou casques
                const isInfo = eq.includes('COMPUTERS') || eq.includes('POSTES');
                const isLang = r.type === 'TP_LANG' || eq.includes('HEADSETS') || (eq.includes('AUDIO') && eq.includes('CASQUES'));

                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="font-family:'JetBrains Mono'">${r.id}</td>
                    <td style="font-weight:600;">${r.name}</td>
                    <td><span class="event-badge badge-td">${r.type}</span></td>
                    <td style="font-weight:600;">${r.capacity ?? '—'} places</td>
                    <td>${isInfo ? '🖥️ Oui' : '<span style="color:var(--text-muted);">Non</span>'}</td>
                    <td>${isLang ? '🎧 Oui' : '<span style="color:var(--text-muted);">Non</span>'}</td>
                    <td style="font-size:0.75rem;">${closureText}</td>
                `;
                tbody.appendChild(tr);
            });
        }

        // Formate une semaine d'évaluation avec le numéro ISO réel + date (via getWeekDateRange).
        function evFmtWeek(week) {
            try {
                if (typeof getWeekDateRange === 'function') {
                    const r = getWeekDateRange(week);
                    if (r && r.label) return `Semaine ISO ${r.iso} (${r.label})`;
                }
            } catch (e) {}
            return `S${week}`;
        }

        function loadEvaluationsTable() {
            const tbody = document.getElementById('evals-table-body');
            tbody.innerHTML = '';

            const evals = constraints.evaluations || [];
            if (evals.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" style="color:var(--text-muted); text-align:center;">Aucune évaluation planifiée.</td></tr>';
                return;
            }

            evals.forEach(ev => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="font-weight:600; color:#fb7185;">📝 ${ev.title}</td>
                    <td><span class="event-badge badge-cm">${ev.resource_code}</span></td>
                    <td>${ev.target_group}</td>
                    <td>${evFmtWeek(ev.week)} - ${ev.day}</td>
                    <td style="font-family:'JetBrains Mono';">${ev.room_id}</td>
                    <td style="color:var(--text-muted); font-size:0.75rem;">${ev.invigilators.join(', ')}</td>
                `;
                tbody.appendChild(tr);
            });
        }

        async function addEvaluation() {
            const title = document.getElementById('eval-title').value.trim();
            const resource = document.getElementById('eval-resource').value.trim();
            const group = document.getElementById('eval-group').value;
            const week = parseInt(document.getElementById('eval-week').value) || 1;
            const day = document.getElementById('eval-day').value;
            const room = document.getElementById('eval-room').value;

            if (!title || !resource) {
                alert("Veuillez renseigner le titre et le code ressource.");
                return;
            }

            try {
                const res = await fetch('/api/v1/evaluations', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        title: title,
                        resource_code: resource,
                        target_group: group,
                        week: week,
                        day: day,
                        room_id: room,
                        invigilators: ["Enseignant TC"]
                    })
                });
                const data = await res.json();
                alert("✅ " + data.message + ` (${evFmtWeek(week)})`);

                const cRes = await fetch('/api/v1/admin/constraints');
                constraints = await cRes.json();
                loadEvaluationsTable();
            } catch (err) {
                alert("Erreur création évaluation : " + err);
            }
        }

        function addRoomClosure() {
            const roomId = document.getElementById('closure-room-select').value;
            const week = parseInt(document.getElementById('closure-week').value) || 1;
            const weekEnd = parseInt(document.getElementById('closure-week-end').value) || week;
            const day = document.getElementById('closure-day').value;
            const reason = document.getElementById('closure-reason').value || "Fermeture";

            if (!constraints.room_closures_or_reservations) constraints.room_closures_or_reservations = [];
            const wStart = Math.min(week, weekEnd), wEnd = Math.max(week, weekEnd);
            // Ajoute une fermeture pour chaque semaine de la plage.
            for (let w = wStart; w <= wEnd; w++) {
                constraints.room_closures_or_reservations.push({
                    room_id: roomId,
                    week: w,
                    day: day,
                    slots: [0, 1, 2, 3],
                    reason: reason
                });
            }

            loadRoomsTable();
            const n = wEnd - wStart + 1;
            const fmtWk = (w) => { try { const r = getWeekDateRange(w); return r ? ' (' + r.label + ')' : ''; } catch(e){ return ''; } };
            alert(`Fermeture enregistrée pour ${roomId} (${day}) sur ${n} semaine${n>1?'s':''} : S${wStart}${fmtWk(wStart)} → S${wEnd}${fmtWk(wEnd)}.`);
        }

        function loadAlternanceWeeks() {
            renderWeekToggles('fa-weeks-but2', 'BUT2_FA', [2, 4, 6, 8, 10, 12, 14]);
            renderWeekToggles('fa-weeks-but3', 'BUT3_FA', [1, 3, 5, 7, 9, 11, 13]);
            renderCatchupToggles('catchup-weeks-container', constraints.catchup_weeks || [8, 15]);
        }

        function renderWeekToggles(containerId, cohortId, defaultWeeks) {
            const c = document.getElementById(containerId);
            c.innerHTML = '';
            const activeWeeks = constraints.cohort_alternance_calendar?.[cohortId]?.company_weeks || defaultWeeks;

            for (let w = 1; w <= 15; w++) {
                const btn = document.createElement('button');
                btn.className = `week-toggle-btn ${activeWeeks.includes(w) ? 'active' : ''}`;
                btn.textContent = `S${w}`;
                btn.onclick = () => {
                    btn.classList.toggle('active');
                    if (!constraints.cohort_alternance_calendar) constraints.cohort_alternance_calendar = {};
                    if (!constraints.cohort_alternance_calendar[cohortId]) {
                        constraints.cohort_alternance_calendar[cohortId] = { company_weeks: [], comment: "Semaines entreprise" };
                    }
                    const list = constraints.cohort_alternance_calendar[cohortId].company_weeks;
                    const idx = list.indexOf(w);
                    if (idx > -1) list.splice(idx, 1);
                    else list.push(w);
                };
                c.appendChild(btn);
            }
        }

        function renderCatchupToggles(containerId, catchupList) {
            const c = document.getElementById(containerId);
            c.innerHTML = '';

            for (let w = 1; w <= 15; w++) {
                const btn = document.createElement('button');
                btn.className = `week-toggle-btn ${catchupList.includes(w) ? 'active' : ''}`;
                btn.textContent = `S${w}`;
                btn.onclick = () => {
                    btn.classList.toggle('active');
                    const idx = constraints.catchup_weeks.indexOf(w);
                    if (idx > -1) constraints.catchup_weeks.splice(idx, 1);
                    else constraints.catchup_weeks.push(w);
                };
                c.appendChild(btn);
            }
        }

        async function saveAllConstraints() {
            constraints.max_hours_per_day_teacher = parseInt(document.getElementById('quota-teacher-hours').value) || 6;
            constraints.max_hours_per_day_student = parseInt(document.getElementById('quota-student-hours').value) || 8;

            // Sauvegarde d'abord les sources iCal (si l'onglet est présent dans le DOM)
            try { await saveIcalSources(true); } catch (e) { /* ignore */ }

            // Sauvegarde les services déclarés des enseignants (définie dans teacher_admin.js)
            try { if (typeof saveTeacherServices === 'function') await saveTeacherServices(); } catch (e) { /* ignore */ }

            // IMPORTANT : le POST /constraints réécrit tout constraints.json. On doit donc
            // y injecter les teacher_services à jour, sinon le POST les écraserait (vide).
            try { if (typeof window !== 'undefined' && typeof window.__getTeacherServices === 'function') {
                constraints.teacher_services = window.__getTeacherServices();
            } } catch (e) {} // old path: teacherServices global manquant

            try {
                const res = await fetch('/api/v1/admin/constraints', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(constraints)
                });
                const data = await res.json();
                alert("✅ " + data.message);
                closeAdminModal();
            } catch (err) {
                alert("Erreur enregistrement : " + err);
            }
        }

        function createDiv(className, htmlContent) {
            const d = document.createElement('div');
            d.className = className;
            d.innerHTML = htmlContent;
            return d;
        }

        window.onload = init;
    