export type WorkspaceView = "chats" | "projects" | "artifacts" | "agents";
export type MessageRole = "user" | "assistant";

export interface AgentSummary {
  key: string;
  name: string;
  role: string;
  capabilities: string[];
  deliverables: string[];
  dependencies: string[];
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  createdAt: string;
  response?: ConsultationResponse;
  error?: boolean;
}

export interface ConversationSummary {
  id: string;
  title: string;
  projectId: string;
  updatedAt: string;
}

export interface ProjectSummary {
  id: string;
  name: string;
  company: string;
  description: string;
}

export interface ArtifactSummary {
  id: string;
  name: string;
  type: "presentation" | "diagram" | "analysis";
  updatedAt: string;
}

export interface ConsultationRequest {
  company: string;
  goal: string;
  context: {
    conversation_id: string;
    project_id: string;
    attachment_names?: string[];
    client_surface: "chat";
  };
  requested_agents: string[];
}

export interface AgentAssignment {
  agent: string;
  key: string;
  assignment: string;
  dependencies: string[];
}

export interface ExecutionWave {
  wave: number;
  agents: string[];
  parallel: boolean;
}

export interface ConsultationResponse {
  summary: string;
  status: string;
  orchestration: {
    orchestrator: string;
    decision_statement: string;
    selected_agents: string[];
    assignments: AgentAssignment[];
    execution_waves: ExecutionWave[];
    quality_gates: string[];
  };
  details: Array<{
    agent: string;
    key: string;
    role: string;
    status: string;
    assignment: string;
    deliverables: string[];
  }>;
}

export const INITIAL_PROJECTS: ProjectSummary[] = [
  {
    id: "project-general",
    name: "General advisory",
    company: "New engagement",
    description: "Cross-functional consulting workspace",
  },
  {
    id: "project-atlas",
    name: "Atlas expansion",
    company: "Atlas Consumer",
    description: "India market-entry assessment",
  },
  {
    id: "project-northstar",
    name: "Northstar plan",
    company: "Northstar Capital",
    description: "Operating model and portfolio review",
  },
];

export const INITIAL_CONVERSATIONS: ConversationSummary[] = [
  {
    id: "conversation-market-entry",
    title: "India market-entry options",
    projectId: "project-atlas",
    updatedAt: "Today",
  },
  {
    id: "conversation-margin-plan",
    title: "Margin improvement plan",
    projectId: "project-northstar",
    updatedAt: "Yesterday",
  },
  {
    id: "conversation-board-deck",
    title: "Board strategy presentation",
    projectId: "project-general",
    updatedAt: "Jun 23",
  },
  {
    id: "conversation-risk-map",
    title: "Regulatory risk workflow",
    projectId: "project-atlas",
    updatedAt: "Jun 21",
  },
];

export const INITIAL_ARTIFACTS: ArtifactSummary[] = [
  {
    id: "artifact-deck",
    name: "Market entry executive deck",
    type: "presentation",
    updatedAt: "Today",
  },
  {
    id: "artifact-workflow",
    name: "Decision workflow",
    type: "diagram",
    updatedAt: "Yesterday",
  },
];
