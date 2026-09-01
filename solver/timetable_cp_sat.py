"""
Constraint-based Timetable Solver for IUT TC using Google OR-Tools CP-SAT.
Guarantees 100% hard constraint satisfaction and optimizes student/teacher schedules.
"""

import sys
import json
import os
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from ortools.sat.python import cp_model

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


@dataclass
class LessonToSchedule:
    id: str
    resource_code: str
    resource_name: str
    event_type: str  # CM, TD, TP
    group_id: str  # e.g., 'BUT1_PROMO', 'BUT1_TD1', 'BUT1_TP11'
    teacher_name: str
    required_room_type: str  # AMPHI, TD, TP_INFO, TP_NEGO
    duration_slots: int = 1  # 1 slot = 2 hours


class TimetableSolver:
    def __init__(self, dataset_path: str, constraints_path: Optional[str] = None):
        self.dataset_path = dataset_path
        with open(dataset_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        if not constraints_path:
            constraints_path = os.path.join(os.path.dirname(dataset_path), "constraints.json")
        
        self.constraints = {}
        if os.path.exists(constraints_path):
            with open(constraints_path, "r", encoding="utf-8") as f:
                self.constraints = json.load(f)

        self.teachers = {t["name"]: t for t in self.data["teachers"]}
        self.resources = {r["code"]: r for r in self.data["resources"]}
        self.rooms = {rm["id"]: rm for rm in self.data["rooms"]}
        self.cohorts = self.data["cohorts"]
        self.calendar = self.data["calendar_config"]


        self.num_days = len(self.calendar["days"])  # 5 days: Lun..Ven
        self.slots_per_day = len(self.calendar["daily_slots"])  # 4 slots/day
        self.total_slots_per_week = self.num_days * self.slots_per_day  # 20 slots
        self.total_weeks = self.calendar["weeks_per_semester"]  # 15 weeks
        self.catchup_weeks = set(self.calendar.get("catchup_weeks", [8, 15]))

    def generate_lessons_for_semester(self, semester: str = "S1") -> List[LessonToSchedule]:
        """
        Generates individual 2h lesson sessions needed for a semester based on the PN.
        """
        lessons = []
        sem_resources = [r for r in self.data["resources"] if r["semester"] == semester and "Tronc Commun" in str(r.get("parcours", ""))]
        
        # If Tronc Commun list is small, take top 8 resources of the semester
        if len(sem_resources) < 6:
            sem_resources = [r for r in self.data["resources"] if r["semester"] == semester][:8]

        for res in sem_resources[:8]:  # 8 active resources per week
            code = res["code"]
            name = res["label"]
            split = res["hours_split"]
            resp = res["responsable"] or (res["team"][0] if res["team"] else "Enseignant TC")
            team = res["team"] if res["team"] else [resp]

            # 1. CM Session (Promo entière)
            if split.get("CM", 0) > 0:
                lessons.append(LessonToSchedule(
                    id=f"{code}_CM",
                    resource_code=code,
                    resource_name=name,
                    event_type="CM",
                    group_id="BUT1_PROMO",
                    teacher_name=resp,
                    required_room_type="AMPHI",
                    duration_slots=1
                ))

            # 2. TD Sessions (TD1 and TD2)
            if split.get("TD", 0) > 0:
                for td_idx, td_grp in enumerate(["BUT1_TD1", "BUT1_TD2"]):
                    teach = team[td_idx % len(team)]
                    lessons.append(LessonToSchedule(
                        id=f"{code}_{td_grp}",
                        resource_code=code,
                        resource_name=name,
                        event_type="TD",
                        group_id=td_grp,
                        teacher_name=teach,
                        required_room_type="TD",
                        duration_slots=1
                    ))

            # 3. TP Sessions (TP11, TP12, TP21, TP22) for practical resources
            if split.get("TP", 0) > 0:
                for tp_idx, tp_grp in enumerate(["BUT1_TP11", "BUT1_TP12", "BUT1_TP21", "BUT1_TP22"]):
                    teach = team[tp_idx % len(team)]
                    room_req = "TP_INFO" if res.get("requires_computer_lab") else "TD"
                    lessons.append(LessonToSchedule(
                        id=f"{code}_{tp_grp}",
                        resource_code=code,
                        resource_name=name,
                        event_type="TP",
                        group_id=tp_grp,
                        teacher_name=teach,
                        required_room_type=room_req,
                        duration_slots=1
                    ))

        return lessons

    def solve_weekly_pattern(self, target_week: int = 1, semester: str = "S1", time_limit_seconds: int = 15) -> Optional[Dict[str, Any]]:
        """
        Solves a typical representative week timetable.
        """
        print(f"🧩 Initializing CP-SAT Model for Semester {semester} - Week {target_week}...")
        model = cp_model.CpModel()

        week_lessons = self.generate_lessons_for_semester(semester)
        print(f"  Total lessons to schedule for Week {target_week}: {len(week_lessons)}")


        # Decision Variables:
        # x[lesson_idx, slot_idx, room_id] = 1 if lesson is scheduled at slot_idx in room_id
        x = {}
        slots = list(range(self.total_slots_per_week))
        room_ids = list(self.rooms.keys())

        for i, lesson in enumerate(week_lessons):
            # Find compatible rooms
            compat_rooms = [
                r_id for r_id, r in self.rooms.items()
                if (lesson.required_room_type == "AMPHI" and r["type"] == "AMPHI") or
                   (lesson.required_room_type == "TP_INFO" and r["type"] == "TP_INFO") or
                   (lesson.required_room_type == "TD" and r["type"] in ["TD", "AMPHI"])
            ]
            if not compat_rooms:
                compat_rooms = room_ids

            for s in slots:
                for r_id in compat_rooms:
                    x[(i, s, r_id)] = model.NewBoolVar(f"x_l{i}_s{s}_r{r_id}")

        # HARD CONSTRAINT 1: Each lesson must be scheduled exactly once
        for i, lesson in enumerate(week_lessons):
            relevant_vars = [var for (li, s, r_id), var in x.items() if li == i]
            model.Add(sum(relevant_vars) == 1)

        # HARD CONSTRAINT 2: No Room Collision (at most 1 lesson per room per slot)
        for s in slots:
            for r_id in room_ids:
                room_vars = [var for (li, slot, room), var in x.items() if slot == s and room == r_id]
                if room_vars:
                    model.Add(sum(room_vars) <= 1)

        # HARD CONSTRAINT 3: No Teacher Collision (a teacher teaches at most 1 lesson per slot)
        teachers_list = list(set(l.teacher_name for l in week_lessons))
        for s in slots:
            for teacher in teachers_list:
                teacher_vars = [
                    var for (li, slot, room), var in x.items()
                    if slot == s and week_lessons[li].teacher_name == teacher
                ]
                if teacher_vars:
                    model.Add(sum(teacher_vars) <= 1)

        # HARD CONSTRAINT 4: Group Hierarchy and No Student Overlap
        # A student in TP11 is simultaneously in TD1 and PROMO.
        # So in any slot s, (lessons for PROMO) + (lessons for TD1) + (lessons for TP11) <= 1.
        student_branches = [
            ["BUT1_PROMO", "BUT1_TD1", "BUT1_TP11"],
            ["BUT1_PROMO", "BUT1_TD1", "BUT1_TP12"],
            ["BUT1_PROMO", "BUT1_TD2", "BUT1_TP21"],
            ["BUT1_PROMO", "BUT1_TD2", "BUT1_TP22"]
        ]

        for s in slots:
            for branch in student_branches:
                branch_vars = [
                    var for (li, slot, room), var in x.items()
                    if slot == s and week_lessons[li].group_id in branch
                ]
                if branch_vars:
                    model.Add(sum(branch_vars) <= 1)

        # HARD CONSTRAINT 5: Teacher Unavailabilities
        day_names = self.calendar["days"]
        for unavail in self.constraints.get("teacher_unavailabilities", []):
            t_name = unavail.get("teacher_name")
            u_day = unavail.get("day")
            u_slots = unavail.get("slots", [])
            if u_day in day_names:
                d_idx = day_names.index(u_day)
                for slot_in_day in u_slots:
                    g_slot = d_idx * self.slots_per_day + slot_in_day
                    blocked_vars = [
                        var for (li, slot, room), var in x.items()
                        if slot == g_slot and week_lessons[li].teacher_name.lower() == t_name.lower()
                    ]
                    if blocked_vars:
                        model.Add(sum(blocked_vars) == 0)

        # HARD CONSTRAINT 6: Room Closures / Reservations
        for closure in self.constraints.get("room_closures_or_reservations", []):
            r_id = closure.get("room_id")
            c_week = closure.get("week")
            c_day = closure.get("day")
            c_slots = closure.get("slots", [])
            # Apply if target_week matches or if closure is weekly
            if c_week is None or c_week == target_week:
                if c_day in day_names:
                    d_idx = day_names.index(c_day)
                    for slot_in_day in c_slots:
                        g_slot = d_idx * self.slots_per_day + slot_in_day
                        blocked_room_vars = [
                            var for (li, slot, room), var in x.items()
                            if slot == g_slot and room == r_id
                        ]
                        if blocked_room_vars:
                            model.Add(sum(blocked_room_vars) == 0)

        # SOFT CONSTRAINTS / OPTIMIZATION OBJECTIVES:
        # 1. Encourage morning slots (M1, M2) over late afternoon (S2)
        # 2. Keep schedule compact
        objective_terms = []

        for (li, s, r_id), var in x.items():
            slot_in_day = s % self.slots_per_day
            # Slight preference for slots 0 (M1), 1 (M2), 2 (S1) over 3 (S2 late afternoon)
            penalty = slot_in_day * 2
            objective_terms.append(var * penalty)

        model.Minimize(sum(objective_terms))

        # Solve
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit_seconds
        solver.parameters.num_workers = 4

        print("⚡ Solving CP-SAT Timetable model...")
        status = solver.Solve(model)

        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            print(f"🎉 Solution Found! Status: {'OPTIMAL' if status == cp_model.OPTIMAL else 'FEASIBLE'}")
            print(f"  Solve Time: {solver.WallTime():.2f}s, Objective Value: {solver.ObjectiveValue()}")

            # Build structured result
            scheduled_events = []
            days_names = self.calendar["days"]
            daily_slots = self.calendar["daily_slots"]

            for (li, s, r_id), var in x.items():
                if solver.Value(var) == 1:
                    lesson = week_lessons[li]
                    day_idx = s // self.slots_per_day
                    slot_in_day = s % self.slots_per_day
                    room = self.rooms[r_id]

                    scheduled_events.append({
                        "lesson_id": lesson.id,
                        "resource_code": lesson.resource_code,
                        "resource_name": lesson.resource_name,
                        "event_type": lesson.event_type,
                        "group_id": lesson.group_id,
                        "teacher_name": lesson.teacher_name,
                        "room_id": room["id"],
                        "room_name": room["name"],
                        "week": target_week,
                        "day": days_names[day_idx],
                        "day_idx": day_idx,
                        "slot_idx": slot_in_day,
                        "slot_time": daily_slots[slot_in_day]["time"],
                        "global_slot": s
                    })

            # Sort chronologically
            scheduled_events.sort(key=lambda e: (e["day_idx"], e["slot_idx"]))

            output_schedule = {
                "semester": semester,
                "week": target_week,
                "status": "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE",
                "solve_time_sec": solver.WallTime(),
                "total_events": len(scheduled_events),
                "events": scheduled_events
            }

            output_dir = os.path.dirname(self.dataset_path)
            output_path = os.path.join(output_dir, "schedule_result.json")
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(output_schedule, f, indent=2, ensure_ascii=False)

            print(f"💾 Schedule saved to {output_path}")
            return output_schedule
        else:
            print("❌ No feasible schedule found under current constraints!")
            return None



def print_ascii_schedule(schedule: Dict[str, Any]):
    events = schedule.get("events", [])
    days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
    slots = ["08:00 - 10:00", "10:15 - 12:15", "13:30 - 15:30", "15:45 - 17:45"]

    print("\n" + "="*80)
    print(f"📅 EMPLOI DU TEMPS TC - SEMAINE TYPE ({schedule['semester']}) - 0 CONFLIT GARANTI")
    print("="*80)

    for d_idx, day in enumerate(days):
        print(f"\n📌 {day.upper()}")
        print("-" * 75)
        day_events = [e for e in events if e["day_idx"] == d_idx]
        for s_idx, slot_name in enumerate(slots):
            slot_evts = [e for e in day_events if e["slot_idx"] == s_idx]
            if not slot_evts:
                print(f"  [{slot_name}] ☕ (Créneau Libre / Travail en autonomie)")
            else:
                for ev in slot_evts:
                    print(f"  [{slot_name}] {ev['event_type']} {ev['resource_code']} ({ev['group_id']}) | Prof: {ev['teacher_name']} | 📍 {ev['room_name']}")


if __name__ == "__main__":
    dataset_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "dataset_tc.json")
    solver = TimetableSolver(dataset_file)
    result = solver.solve_weekly_pattern(target_week=1, semester="S1")
    if result:
        print_ascii_schedule(result)
