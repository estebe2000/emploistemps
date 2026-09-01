package emploistemps

// Teacher represents a faculty member with teaching quotas and assignments.
type Teacher struct {
	ID                string   `json:"id"`
	Name              string   `json:"name"`
	MaxHoursPerDay    int      `json:"max_hours_per_day"`
	AssignedResources []string `json:"assigned_resources"`
}

// Resource represents a pedagogical resource from the PN (e.g. R1.01).
type Resource struct {
	Code                string            `json:"code"`
	Label               string            `json:"label"`
	Semester            string            `json:"semester"`
	Parcours            string            `json:"parcours"`
	VolumeTotal         int               `json:"volume_total"`
	HoursSplit          map[string]int    `json:"hours_split"`
	Responsable         string            `json:"responsable"`
	Team                []string          `json:"team"`
	RequiresComputerLab bool              `json:"requires_computer_lab"`
}

// Room represents a classroom, amphi or lab.
type Room struct {
	ID         string   `json:"id"`
	Name       string   `json:"name"`
	Capacity   int      `json:"capacity"`
	Type       string   `json:"type"`
	Equipments []string `json:"equipments"`
}

// Cohort represents a promo (FI or FA).
type Cohort struct {
	ID              string   `json:"id"`
	Name            string   `json:"name"`
	Level           string   `json:"level"`
	Mode            string   `json:"mode"`
	Size            int      `json:"size"`
	GroupsTD        []string `json:"groups_td"`
	GroupsTP        []string `json:"groups_tp"`
	AlternanceWeeks []int    `json:"alternance_weeks"`
}

// ScheduledEvent represents an assigned course slot in the schedule.
type ScheduledEvent struct {
	LessonID     string `json:"lesson_id"`
	ResourceCode string `json:"resource_code"`
	ResourceName string `json:"resource_name"`
	EventType    string `json:"event_type"`
	GroupID      string `json:"group_id"`
	TeacherName  string `json:"teacher_name"`
	RoomID       string `json:"room_id"`
	RoomName     string `json:"room_name"`
	Week         int    `json:"week"`
	Day          string `json:"day"`
	DayIdx       int    `json:"day_idx"`
	SlotIdx      int    `json:"slot_idx"`
	SlotTime     string `json:"slot_time"`
	GlobalSlot   int    `json:"global_slot"`
}

// ScheduleResult is the response from the CP-SAT solver or schedule query.
type ScheduleResult struct {
	Semester     string           `json:"semester"`
	Week         int              `json:"week"`
	Status       string           `json:"status"`
	SolveTimeSec float64          `json:"solve_time_sec"`
	TotalEvents  int              `json:"total_events"`
	Events       []ScheduledEvent `json:"events"`
}

// GenerateRequest options for solving a schedule.
type GenerateRequest struct {
	Semester         string `json:"semester"`
	Week             int    `json:"week"`
	TimeLimitSeconds int    `json:"time_limit_seconds"`
}

// MoveLessonRequest represents a request to move an event.
type MoveLessonRequest struct {
	LessonID        string `json:"lesson_id"`
	TargetDay       string `json:"target_day"`
	TargetSlotIdx   int    `json:"target_slot_idx"`
	TargetRoomID    string `json:"target_room_id,omitempty"`
}

// ConflictCheckResponse represents the outcome of a conflict verification.
type ConflictCheckResponse struct {
	Conflit   bool     `json:"conflit"`
	Autorise  bool     `json:"autorise"`
	Raisons   []string `json:"raisons,omitempty"`
	Message   string   `json:"message"`
}

// FreeSlot represents an available slot for a group and teacher.
type FreeSlot struct {
	Jour    string `json:"jour"`
	SlotIdx int    `json:"slot_idx"`
	Heure   string `json:"heure"`
}

// AIChatRequest represents a query to the AI assistant.
type AIChatRequest struct {
	Prompt string `json:"prompt"`
}

// AIChatResponse represents the response from the AI assistant.
type AIChatResponse struct {
	Response string `json:"response"`
}
