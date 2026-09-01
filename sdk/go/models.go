package emploistemps

// Event represents a single scheduled pedagogical lesson or evaluation in the timetable.
type Event struct {
	LessonID      string  `json:"lesson_id"`
	ResourceCode  string  `json:"resource_code"`
	ResourceName  string  `json:"resource_name"`
	EventType     string  `json:"event_type"` // CM, TD, TP, EVAL
	GroupID       string  `json:"group_id"`
	TeacherName   string  `json:"teacher_name"`
	RoomID        string  `json:"room_id"`
	RoomName      string  `json:"room_name"`
	Week          int     `json:"week"`
	Day           string  `json:"day"`
	DayIdx        int     `json:"day_idx"`
	SlotIdx       int     `json:"slot_idx"`
	SlotTime      string  `json:"slot_time"`
	DurationHours float64 `json:"duration_hours"`
	HetdHours     float64 `json:"hetd_hours"` // 1h CM = 1.5h TD, 4h TP = 3h TD (0.75 ratio)
	IsEvaluation  bool    `json:"is_evaluation"`
	GlobalSlot    int     `json:"global_slot"`
}

// ScheduleResponse / ScheduleResult represents solver generation response.
type ScheduleResponse struct {
	Semester     string  `json:"semester"`
	Week         int     `json:"week"`
	Status       string  `json:"status"` // OPTIMAL, FEASIBLE
	SolveTimeSec float64 `json:"solve_time_sec"`
	TotalEvents  int     `json:"total_events"`
	Events       []Event `json:"events"`
}

type ScheduleResult = ScheduleResponse

// SolverRequest / GenerateRequest configures a CP-SAT solving run.
type SolverRequest struct {
	Semester         string `json:"semester"`
	Week             int    `json:"week"`
	TimeLimitSeconds int    `json:"time_limit_seconds"`
}

type GenerateRequest = SolverRequest

// MoveLessonRequest represents a request to move or test moving an event.
type MoveLessonRequest struct {
	LessonID       string `json:"lesson_id"`
	TargetDay      string `json:"target_day"`
	TargetSlotIdx  int    `json:"target_slot_idx"`
	TargetRoomID   string `json:"target_room_id"`
}

// ConflictCheckResponse is returned when checking or performing a move.
type ConflictCheckResponse struct {
	Conflit bool     `json:"conflit"`
	Raisons []string `json:"raisons,omitempty"`
	Message string   `json:"message"`
}

// FreeSlot represents an available slot for both teacher and student group.
type FreeSlot struct {
	Jour    string `json:"jour"`
	Heure   string `json:"heure"`
	SlotIdx int    `json:"slot_idx"`
}

// TeacherWorkloadItem contains statutory vs planned HETD breakdown for a teacher.
type TeacherWorkloadItem struct {
	TeacherID             string  `json:"teacher_id"`
	TeacherName           string  `json:"teacher_name"`
	Statut                string  `json:"statut"` // PRAG, MCF, VACATAIRE
	ServiceStatutaireHetd float64 `json:"service_statutaire_hetd"`
	SemaineHeuresCM       float64 `json:"semaine_heures_cm"`
	SemaineHeuresTD       float64 `json:"semaine_heures_td"`
	SemaineHeuresTP       float64 `json:"semaine_heures_tp"`
	SemaineTotalHetd      float64 `json:"semaine_total_hetd"`
	SemestreEstimeHetd    float64 `json:"semestre_estime_hetd"`
	DeltaHetd             float64 `json:"delta_hetd"`
	Status                string  `json:"status"` // ÉQUILIBRÉ, HEURES_SUP, SOUS_SERVICE
	NbCoursPlanifies      int     `json:"nb_cours_planifies"`
}

// TeacherWorkloadResponse is the payload for GET /api/v1/teachers/workload.
type TeacherWorkloadResponse struct {
	HetdRule string                `json:"hetd_rule"`
	Teachers []TeacherWorkloadItem `json:"teachers"`
}

// Evaluation represents a scheduled DS / Partiel / Exam.
type Evaluation struct {
	ID            string   `json:"id"`
	Title         string   `json:"title"`
	ResourceCode  string   `json:"resource_code"`
	TargetGroup   string   `json:"target_group"`
	Week          int      `json:"week"`
	Day           string   `json:"day"`
	SlotIdx       int      `json:"slot_idx"`
	RoomID        string   `json:"room_id"`
	DurationHours float64  `json:"duration_hours"`
	Invigilators  []string `json:"invigilators"`
}

// QuickActionRequest represents contextual right-click actions on events.
type QuickActionRequest struct {
	Action     string `json:"action"` // MOVE, CHANGE_ROOM, CHANGE_TEACHER, CANCEL, CONVERT_EVAL
	LessonID   string `json:"lesson_id"`
	NewRoomID  string `json:"new_room_id,omitempty"`
	NewTeacher string `json:"new_teacher,omitempty"`
}

// AIChatRequest is sent to the LLM copilot endpoint.
type AIChatRequest struct {
	Prompt string `json:"prompt"`
}

// AIChatResponse contains the assistant message.
type AIChatResponse struct {
	Response string `json:"response"`
	Status   string `json:"status"`
}
