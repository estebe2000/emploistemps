package emploistemps

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"time"
)

// Client is the Go SDK client for the Emplois du Temps scheduling and AI service.
type Client struct {
	BaseURL    string
	HTTPClient *http.Client
	APIKey     string
}

// Option configures the Client.
type Option func(*Client)

// WithHTTPClient sets a custom http.Client.
func WithHTTPClient(httpClient *http.Client) Option {
	return func(c *Client) {
		c.HTTPClient = httpClient
	}
}

// WithAPIKey sets an API authentication key if enabled.
func WithAPIKey(key string) Option {
	return func(c *Client) {
		c.APIKey = key
	}
}

// NewClient creates a new Emplois du Temps Go client.
func NewClient(baseURL string, opts ...Option) *Client {
	if baseURL == "" {
		baseURL = "http://localhost:8000"
	}
	c := &Client{
		BaseURL: baseURL,
		HTTPClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
	for _, opt := range opts {
		opt(c)
	}
	return c
}

func (c *Client) doRequest(ctx context.Context, method, path string, bodyIn any, bodyOut any) error {
	var bodyReader io.Reader
	if bodyIn != nil {
		data, err := json.Marshal(bodyIn)
		if err != nil {
			return fmt.Errorf("marshal request body: %w", err)
		}
		bodyReader = bytes.NewReader(data)
	}

	reqURL := fmt.Sprintf("%s%s", c.BaseURL, path)
	req, err := http.NewRequestWithContext(ctx, method, reqURL, bodyReader)
	if err != nil {
		return fmt.Errorf("create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")
	if c.APIKey != "" {
		req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.APIKey))
	}

	resp, err := c.HTTPClient.Do(req)
	if err != nil {
		return fmt.Errorf("do request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		respBody, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("api error (status %d): %s", resp.StatusCode, string(respBody))
	}

	if bodyOut != nil {
		if err := json.NewDecoder(resp.Body).Decode(bodyOut); err != nil {
			return fmt.Errorf("decode response: %w", err)
		}
	}
	return nil
}

// Health checks the service availability.
func (c *Client) Health(ctx context.Context) (map[string]string, error) {
	var res map[string]string
	err := c.doRequest(ctx, http.MethodGet, "/health", nil, &res)
	return res, err
}

// GenerateSchedule triggers the CP-SAT solver to generate an optimal conflict-free schedule.
func (c *Client) GenerateSchedule(ctx context.Context, req GenerateRequest) (*ScheduleResult, error) {
	var res ScheduleResult
	err := c.doRequest(ctx, http.MethodPost, "/api/v1/solver/generate", req, &res)
	if err != nil {
		return nil, err
	}
	return &res, nil
}

// GetSchedule retrieves the current schedule, optionally filtered by group, teacher, or room.
func (c *Client) GetSchedule(ctx context.Context, groupID, teacher, room string) (*ScheduleResult, error) {
	params := url.Values{}
	if groupID != "" {
		params.Set("group_id", groupID)
	}
	if teacher != "" {
		params.Set("teacher", teacher)
	}
	if room != "" {
		params.Set("room", room)
	}

	path := "/api/v1/schedule"
	if len(params) > 0 {
		path += "?" + params.Encode()
	}

	var res ScheduleResult
	err := c.doRequest(ctx, http.MethodGet, path, nil, &res)
	if err != nil {
		return nil, err
	}
	return &res, nil
}

// VerifyConflict checks whether moving a lesson to a target slot/room would create a conflict.
func (c *Client) VerifyConflict(ctx context.Context, req MoveLessonRequest) (*ConflictCheckResponse, error) {
	var res ConflictCheckResponse
	err := c.doRequest(ctx, http.MethodPost, "/api/v1/schedule/verify-conflict", req, &res)
	if err != nil {
		return nil, err
	}
	return &res, nil
}

// MoveLesson moves a lesson to a new slot and room.
func (c *Client) MoveLesson(ctx context.Context, req MoveLessonRequest) (*ConflictCheckResponse, error) {
	var res ConflictCheckResponse
	err := c.doRequest(ctx, http.MethodPost, "/api/v1/schedule/move", req, &res)
	if err != nil {
		return nil, err
	}
	return &res, nil
}

// FindFreeSlots finds slots where both teacher and group are free.
func (c *Client) FindFreeSlots(ctx context.Context, teacher, groupID string) ([]FreeSlot, error) {
	params := url.Values{}
	params.Set("teacher", teacher)
	params.Set("group_id", groupID)

	path := fmt.Sprintf("/api/v1/schedule/free-slots?%s", params.Encode())
	var res []FreeSlot
	err := c.doRequest(ctx, http.MethodGet, path, nil, &res)
	if err != nil {
		return nil, err
	}
	return res, nil
}

// AskAI asks the AI Assistant (Albert API) a natural language question or command.
func (c *Client) AskAI(ctx context.Context, prompt string) (string, error) {
	req := AIChatRequest{Prompt: prompt}
	var res AIChatResponse
	err := c.doRequest(ctx, http.MethodPost, "/api/v1/ai/chat", req, &res)
	if err != nil {
		return "", err
	}
	return res.Response, nil
}

// GetTeacherWorkload retrieves statutory vs planned HETD workloads for all teachers.
func (c *Client) GetTeacherWorkload(ctx context.Context) (*TeacherWorkloadResponse, error) {
	var res TeacherWorkloadResponse
	err := c.doRequest(ctx, http.MethodGet, "/api/v1/teachers/workload", nil, &res)
	if err != nil {
		return nil, err
	}
	return &res, nil
}

// ExecuteQuickAction sends a contextual action (MOVE, CHANGE_ROOM, CHANGE_TEACHER, CANCEL, CONVERT_EVAL).
func (c *Client) ExecuteQuickAction(ctx context.Context, req QuickActionRequest) (map[string]any, error) {
	var res map[string]any
	err := c.doRequest(ctx, http.MethodPost, "/api/v1/schedule/quick-action", req, &res)
	if err != nil {
		return nil, err
	}
	return res, nil
}

