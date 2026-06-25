"use client";

import {
  Archive,
  ArrowUp,
  BriefcaseBusiness,
  Check,
  ChevronDown,
  Database,
  FileChartColumn,
  FileText,
  FolderKanban,
  Layers3,
  Menu,
  MessageSquareText,
  Network,
  PanelLeftClose,
  Paperclip,
  Plus,
  Presentation,
  Search,
  Settings2,
  Sparkles,
  SquareActivity,
  UsersRound,
  X,
} from "lucide-react";
import Link from "next/link";
import {
  ChangeEvent,
  FormEvent,
  memo,
  useDeferredValue,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import styles from "@/components/ChatWorkspace.module.css";
import { getAgents, getApiHealth, submitConsultation } from "@/lib/api";
import {
  AgentSummary,
  ArtifactSummary,
  ChatMessage,
  ConversationSummary,
  INITIAL_ARTIFACTS,
  INITIAL_CONVERSATIONS,
  INITIAL_PROJECTS,
  ProjectSummary,
  WorkspaceView,
} from "@/lib/chat";

const SUGGESTIONS = [
  {
    label: "Assess a market",
    prompt:
      "Assess the attractiveness of entering a new market, including customer segments, competition, economics, and major risks.",
    icon: SquareActivity,
  },
  {
    label: "Build a strategy",
    prompt:
      "Develop strategic options for the next three years and recommend a practical execution roadmap.",
    icon: BriefcaseBusiness,
  },
  {
    label: "Review financials",
    prompt:
      "Review financial performance, forecast the base and downside cases, and identify the strongest value-creation levers.",
    icon: FileChartColumn,
  },
  {
    label: "Create an executive deck",
    prompt:
      "Create a board-ready presentation plan with a clear storyline, charts, recommendations, and implementation roadmap.",
    icon: Presentation,
  },
  {
    label: "Map a workflow",
    prompt:
      "Map the operating workflow, decision points, controls, and handoffs as a Mermaid diagram.",
    icon: Network,
  },
];

const AGENT_ACCENTS = [
  "#ea7657",
  "#39a891",
  "#e4aa45",
  "#6e8fe8",
  "#c67bb0",
  "#64a7c8",
];

function createId(prefix: string) {
  return `${prefix}-${crypto.randomUUID()}`;
}

function greeting() {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

export function ChatWorkspace() {
  const [view, setView] = useState<WorkspaceView>("chats");
  const [greetingText, setGreetingText] = useState("Hello");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [search, setSearch] = useState("");
  const deferredSearch = useDeferredValue(search);
  const [projects, setProjects] = useState(INITIAL_PROJECTS);
  const [activeProjectId, setActiveProjectId] = useState(
    INITIAL_PROJECTS[0].id,
  );
  const [conversations, setConversations] = useState(INITIAL_CONVERSATIONS);
  const [activeConversationId, setActiveConversationId] = useState(
    createId("conversation"),
  );
  const [artifacts] = useState(INITIAL_ARTIFACTS);
  const [agents, setAgents] = useState<AgentSummary[]>([]);
  const [selectedAgent, setSelectedAgent] = useState("auto");
  const [agentMenuOpen, setAgentMenuOpen] = useState(false);
  const [projectMenuOpen, setProjectMenuOpen] = useState(false);
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [attachments, setAttachments] = useState<File[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  const activeProject =
    projects.find((project) => project.id === activeProjectId) ?? projects[0];

  useEffect(() => {
    const controller = new AbortController();
    Promise.all([
      getApiHealth(controller.signal),
      getAgents(controller.signal).catch(() => []),
    ]).then(([online, agentList]) => {
      setApiOnline(online);
      setAgents(agentList);
    });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    setGreetingText(greeting());
  }, []);

  useEffect(() => {
    if (!scrollRef.current) return;
    scrollRef.current.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, submitting]);

  const filteredConversations = useMemo(() => {
    const term = deferredSearch.trim().toLowerCase();
    if (!term) return conversations;
    return conversations.filter((conversation) =>
      conversation.title.toLowerCase().includes(term),
    );
  }, [conversations, deferredSearch]);

  const selectedAgentName =
    selectedAgent === "auto"
      ? "Auto orchestrate"
      : agents.find((agent) => agent.key === selectedAgent)?.name ??
        "Auto orchestrate";

  const startNewChat = () => {
    abortRef.current?.abort();
    setActiveConversationId(createId("conversation"));
    setMessages([]);
    setDraft("");
    setAttachments([]);
    setSelectedAgent("auto");
    setView("chats");
    setSidebarOpen(false);
    requestAnimationFrame(() => textareaRef.current?.focus());
  };

  const handleFiles = (event: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files ?? []).slice(0, 4);
    setAttachments((current) => [...current, ...files].slice(0, 4));
    event.target.value = "";
  };

  const submit = async (event?: FormEvent) => {
    event?.preventDefault();
    const prompt = draft.trim();
    if (!prompt || submitting) return;

    const userMessage: ChatMessage = {
      id: createId("message"),
      role: "user",
      content: prompt,
      createdAt: new Date().toISOString(),
    };
    setMessages((current) => [...current, userMessage]);
    setDraft("");
    setSubmitting(true);

    const title = prompt.length > 54 ? `${prompt.slice(0, 54)}...` : prompt;
    setConversations((current) => {
      const exists = current.some(
        (conversation) => conversation.id === activeConversationId,
      );
      if (exists) return current;
      return [
        {
          id: activeConversationId,
          title,
          projectId: activeProject.id,
          updatedAt: "Now",
        },
        ...current,
      ];
    });

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const response = await submitConsultation(
        {
          company: activeProject.company,
          goal: prompt,
          context: {
            conversation_id: activeConversationId,
            project_id: activeProject.id,
            attachment_names: attachments.map((file) => file.name),
            client_surface: "chat",
          },
          requested_agents:
            selectedAgent === "auto" ? [] : [selectedAgent],
        },
        controller.signal,
      );
      setMessages((current) => [
        ...current,
        {
          id: createId("message"),
          role: "assistant",
          content: response.orchestration.decision_statement,
          response,
          createdAt: new Date().toISOString(),
        },
      ]);
      setAttachments([]);
      setApiOnline(true);
    } catch (error) {
      if (controller.signal.aborted) return;
      setMessages((current) => [
        ...current,
        {
          id: createId("message"),
          role: "assistant",
          content:
            error instanceof Error
              ? error.message
              : "The consultation request could not be completed.",
          error: true,
          createdAt: new Date().toISOString(),
        },
      ]);
      setApiOnline(false);
    } finally {
      setSubmitting(false);
      abortRef.current = null;
    }
  };

  const chooseConversation = (conversation: ConversationSummary) => {
    setActiveConversationId(conversation.id);
    setActiveProjectId(conversation.projectId);
    setMessages([]);
    setView("chats");
    setSidebarOpen(false);
  };

  return (
    <div
      className={`${styles.shell} ${
        sidebarCollapsed ? styles.sidebarCollapsed : ""
      }`}
    >
      <Sidebar
        activeView={view}
        artifacts={artifacts}
        conversations={filteredConversations}
        collapsed={sidebarCollapsed}
        mobileOpen={sidebarOpen}
        search={search}
        onCloseMobile={() => setSidebarOpen(false)}
        onCollapse={() => setSidebarCollapsed((current) => !current)}
        onConversation={chooseConversation}
        onNavigate={(nextView) => {
          setView(nextView);
          setSidebarOpen(false);
        }}
        onNewChat={startNewChat}
        onSearch={setSearch}
      />

      {sidebarOpen && (
        <button
          className={styles.backdrop}
          type="button"
          aria-label="Dismiss navigation backdrop"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <main className={styles.main}>
        <header className={styles.topbar}>
          <button
            className={styles.mobileMenu}
            type="button"
            title="Open navigation"
            aria-label="Open navigation"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu size={19} />
          </button>

          <div className={styles.projectPickerWrap}>
            <button
              className={styles.projectPicker}
              type="button"
              aria-expanded={projectMenuOpen}
              onClick={() => setProjectMenuOpen((current) => !current)}
            >
              <span>
                <small>Project</small>
                <strong>{activeProject.name}</strong>
              </span>
              <ChevronDown size={15} />
            </button>
            {projectMenuOpen && (
              <div className={styles.popover}>
                {projects.map((project) => (
                  <button
                    key={project.id}
                    type="button"
                    onClick={() => {
                      setActiveProjectId(project.id);
                      setProjectMenuOpen(false);
                    }}
                  >
                    <span>
                      <strong>{project.name}</strong>
                      <small>{project.company}</small>
                    </span>
                    {project.id === activeProject.id && <Check size={15} />}
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className={styles.systemStatus}>
            <span
              className={`${styles.statusDot} ${
                apiOnline === true
                  ? styles.online
                  : apiOnline === false
                    ? styles.offline
                    : ""
              }`}
            />
            <span>
              {apiOnline === null
                ? "Connecting"
                : apiOnline
                  ? "FastAPI connected"
                  : "Backend offline"}
            </span>
            <span className={styles.memoryHint}>
              <Database size={13} />
              Server memory
            </span>
          </div>
        </header>

        {view === "chats" ? (
          <section className={styles.chatSurface}>
            {messages.length === 0 ? (
              <EmptyChat
                draft={draft}
                greetingText={greetingText}
                onDraft={setDraft}
                onSuggestion={(prompt) => {
                  setDraft(prompt);
                  requestAnimationFrame(() => textareaRef.current?.focus());
                }}
                submit={submit}
                textareaRef={textareaRef}
              >
                <ComposerTools
                  agentMenuOpen={agentMenuOpen}
                  agents={agents}
                  attachments={attachments}
                  disabled={!draft.trim() || submitting}
                  selectedAgent={selectedAgent}
                  selectedAgentName={selectedAgentName}
                  submitting={submitting}
                  onAgentMenu={() =>
                    setAgentMenuOpen((current) => !current)
                  }
                  onAttach={() => fileInputRef.current?.click()}
                  onRemoveAttachment={(name) =>
                    setAttachments((current) =>
                      current.filter((file) => file.name !== name),
                    )
                  }
                  onSelectAgent={(agent) => {
                    setSelectedAgent(agent);
                    setAgentMenuOpen(false);
                  }}
                />
              </EmptyChat>
            ) : (
              <div className={styles.conversation}>
                <div className={styles.messageScroll} ref={scrollRef}>
                  <div className={styles.messageList}>
                    {messages.map((message) => (
                      <Message
                        key={message.id}
                        message={message}
                        onFollowup={(prompt) => {
                          setDraft(prompt);
                          requestAnimationFrame(() =>
                            textareaRef.current?.focus(),
                          );
                        }}
                      />
                    ))}
                    {submitting && <ThinkingState />}
                  </div>
                </div>
                <div className={styles.dockedComposer}>
                  <Composer
                    draft={draft}
                    onDraft={setDraft}
                    submit={submit}
                    textareaRef={textareaRef}
                  >
                    <ComposerTools
                      agentMenuOpen={agentMenuOpen}
                      agents={agents}
                      attachments={attachments}
                      disabled={!draft.trim() || submitting}
                      selectedAgent={selectedAgent}
                      selectedAgentName={selectedAgentName}
                      submitting={submitting}
                      onAgentMenu={() =>
                        setAgentMenuOpen((current) => !current)
                      }
                      onAttach={() => fileInputRef.current?.click()}
                      onRemoveAttachment={(name) =>
                        setAttachments((current) =>
                          current.filter((file) => file.name !== name),
                        )
                      }
                      onSelectAgent={(agent) => {
                        setSelectedAgent(agent);
                        setAgentMenuOpen(false);
                      }}
                    />
                  </Composer>
                </div>
              </div>
            )}

            <input
              ref={fileInputRef}
              className={styles.hiddenInput}
              type="file"
              multiple
              accept=".pdf,.doc,.docx,.xlsx,.xls,.csv,.txt,.pptx"
              onChange={handleFiles}
            />
          </section>
        ) : (
          <WorkspacePanel
            agents={agents}
            artifacts={artifacts}
            projects={projects}
            view={view}
            onNewProject={() =>
              setProjects((current) => [
                ...current,
                {
                  id: createId("project"),
                  name: `Project ${current.length + 1}`,
                  company: "New company",
                  description: "New consulting workspace",
                },
              ])
            }
          />
        )}
      </main>
    </div>
  );
}

const Sidebar = memo(function Sidebar({
  activeView,
  artifacts,
  conversations,
  collapsed,
  mobileOpen,
  search,
  onCloseMobile,
  onCollapse,
  onConversation,
  onNavigate,
  onNewChat,
  onSearch,
}: {
  activeView: WorkspaceView;
  artifacts: ArtifactSummary[];
  conversations: ConversationSummary[];
  collapsed: boolean;
  mobileOpen: boolean;
  search: string;
  onCloseMobile: () => void;
  onCollapse: () => void;
  onConversation: (conversation: ConversationSummary) => void;
  onNavigate: (view: WorkspaceView) => void;
  onNewChat: () => void;
  onSearch: (value: string) => void;
}) {
  const navigation = [
    { id: "chats" as const, label: "Consultations", icon: MessageSquareText },
    { id: "projects" as const, label: "Projects", icon: FolderKanban },
    { id: "artifacts" as const, label: "Artifacts", icon: Archive },
    { id: "agents" as const, label: "Specialist agents", icon: UsersRound },
  ];

  return (
    <aside
      className={`${styles.sidebar} ${
        mobileOpen ? styles.sidebarMobileOpen : ""
      }`}
    >
      <div className={styles.sidebarHeader}>
        <div className={styles.wordmark}>
          <span>K</span>
          {!collapsed && <strong>KapexAI</strong>}
        </div>
        <button
          className={styles.iconButton}
          type="button"
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          onClick={onCollapse}
        >
          <PanelLeftClose size={18} />
        </button>
        <button
          className={styles.mobileClose}
          type="button"
          title="Close navigation"
          aria-label="Close navigation"
          onClick={onCloseMobile}
        >
          <X size={19} />
        </button>
      </div>

      <button className={styles.newChat} type="button" onClick={onNewChat}>
        <Plus size={17} />
        {!collapsed && <span>New consultation</span>}
      </button>

      <nav className={styles.navigation} aria-label="Primary">
        {navigation.map((item) => {
          const Icon = item.icon;
          const badge =
            item.id === "artifacts" && artifacts.length > 0
              ? artifacts.length
              : undefined;
          return (
            <button
              className={`${styles.navItem} ${
                activeView === item.id ? styles.navItemActive : ""
              }`}
              key={item.id}
              type="button"
              title={collapsed ? item.label : undefined}
              onClick={() => onNavigate(item.id)}
            >
              <Icon size={18} />
              {!collapsed && <span>{item.label}</span>}
              {!collapsed && badge && <small>{badge}</small>}
            </button>
          );
        })}
        <Link className={styles.navItem} href="/scenario">
          <SquareActivity size={18} />
          {!collapsed && <span>Scenario lab</span>}
        </Link>
      </nav>

      {!collapsed && (
        <>
          <div className={styles.searchBox}>
            <Search size={15} />
            <input
              aria-label="Search consultations"
              placeholder="Search consultations"
              value={search}
              onChange={(event) => onSearch(event.target.value)}
            />
          </div>

          <div className={styles.recents}>
            <div className={styles.sectionLabel}>
              <span>Recent</span>
              <Settings2 size={14} />
            </div>
            <div className={styles.recentList}>
              {conversations.map((conversation) => (
                <button
                  key={conversation.id}
                  type="button"
                  onClick={() => onConversation(conversation)}
                >
                  <span>{conversation.title}</span>
                  <small>{conversation.updatedAt}</small>
                </button>
              ))}
              {conversations.length === 0 && (
                <p className={styles.emptyRecent}>No matching consultations</p>
              )}
            </div>
          </div>
        </>
      )}

      <div className={styles.profile}>
        <span className={styles.avatar}>KH</span>
        {!collapsed && (
          <span>
            <strong>King Himkesh</strong>
            <small>Workspace owner</small>
          </span>
        )}
        {!collapsed && <ChevronDown size={14} />}
      </div>
    </aside>
  );
});

function EmptyChat({
  children,
  draft,
  greetingText,
  onDraft,
  onSuggestion,
  submit,
  textareaRef,
}: {
  children: React.ReactNode;
  draft: string;
  greetingText: string;
  onDraft: (value: string) => void;
  onSuggestion: (prompt: string) => void;
  submit: (event?: FormEvent) => void;
  textareaRef: React.RefObject<HTMLTextAreaElement | null>;
}) {
  return (
    <div className={styles.emptyChat}>
      <div className={styles.intro}>
        <span className={styles.spark}>
          <Sparkles size={30} />
        </span>
        <div>
          <p>{greetingText}, King Himkesh</p>
          <h1>What should we solve today?</h1>
        </div>
      </div>
      <Composer
        draft={draft}
        onDraft={onDraft}
        submit={submit}
        textareaRef={textareaRef}
      >
        {children}
      </Composer>
      <div className={styles.suggestions}>
        {SUGGESTIONS.map((suggestion) => {
          const Icon = suggestion.icon;
          return (
            <button
              key={suggestion.label}
              type="button"
              onClick={() => onSuggestion(suggestion.prompt)}
            >
              <Icon size={16} />
              {suggestion.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function Composer({
  children,
  draft,
  onDraft,
  submit,
  textareaRef,
}: {
  children: React.ReactNode;
  draft: string;
  onDraft: (value: string) => void;
  submit: (event?: FormEvent) => void;
  textareaRef: React.RefObject<HTMLTextAreaElement | null>;
}) {
  return (
    <form className={styles.composer} onSubmit={submit}>
      <textarea
        ref={textareaRef}
        aria-label="Consultation request"
        placeholder="Describe the decision, problem, or deliverable..."
        rows={3}
        value={draft}
        onChange={(event) => onDraft(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            submit();
          }
        }}
      />
      {children}
    </form>
  );
}

function ComposerTools({
  agentMenuOpen,
  agents,
  attachments,
  disabled,
  selectedAgent,
  selectedAgentName,
  submitting,
  onAgentMenu,
  onAttach,
  onRemoveAttachment,
  onSelectAgent,
}: {
  agentMenuOpen: boolean;
  agents: AgentSummary[];
  attachments: File[];
  disabled: boolean;
  selectedAgent: string;
  selectedAgentName: string;
  submitting: boolean;
  onAgentMenu: () => void;
  onAttach: () => void;
  onRemoveAttachment: (name: string) => void;
  onSelectAgent: (agent: string) => void;
}) {
  return (
    <>
      {attachments.length > 0 && (
        <div className={styles.attachments}>
          {attachments.map((file) => (
            <span key={`${file.name}-${file.size}`}>
              <FileText size={13} />
              {file.name}
              <button
                type="button"
                title={`Remove ${file.name}`}
                aria-label={`Remove ${file.name}`}
                onClick={() => onRemoveAttachment(file.name)}
              >
                <X size={12} />
              </button>
            </span>
          ))}
        </div>
      )}
      <div className={styles.composerFooter}>
        <div className={styles.composerActions}>
          <button
            className={styles.toolButton}
            type="button"
            title="Attach context files"
            aria-label="Attach context files"
            onClick={onAttach}
          >
            <Paperclip size={18} />
          </button>
          <div className={styles.agentPickerWrap}>
            <button
              className={styles.agentPicker}
              type="button"
              aria-expanded={agentMenuOpen}
              onClick={onAgentMenu}
            >
              <Layers3 size={15} />
              <span>{selectedAgentName}</span>
              <ChevronDown size={14} />
            </button>
            {agentMenuOpen && (
              <div className={styles.agentMenu}>
                <button
                  type="button"
                  onClick={() => onSelectAgent("auto")}
                >
                  <span
                    className={styles.agentMark}
                    style={{ backgroundColor: "#ea7657" }}
                  >
                    <Sparkles size={14} />
                  </span>
                  <span>
                    <strong>Auto orchestrate</strong>
                    <small>Route to the right specialist team</small>
                  </span>
                  {selectedAgent === "auto" && <Check size={15} />}
                </button>
                {agents
                  .filter((agent) => agent.key !== "orchestrator")
                  .map((agent, index) => (
                    <button
                      key={agent.key}
                      type="button"
                      onClick={() => onSelectAgent(agent.key)}
                    >
                      <span
                        className={styles.agentMark}
                        style={{
                          backgroundColor:
                            AGENT_ACCENTS[index % AGENT_ACCENTS.length],
                        }}
                      >
                        {agent.name.charAt(0)}
                      </span>
                      <span>
                        <strong>{agent.name.replace(" Agent", "")}</strong>
                        <small>{agent.role}</small>
                      </span>
                      {selectedAgent === agent.key && <Check size={15} />}
                    </button>
                  ))}
              </div>
            )}
          </div>
        </div>
        <button
          className={styles.sendButton}
          type="submit"
          title="Send consultation"
          aria-label="Send consultation"
          disabled={disabled}
        >
          {submitting ? (
            <span className={styles.spinner} />
          ) : (
            <ArrowUp size={18} />
          )}
        </button>
      </div>
    </>
  );
}

function Message({
  message,
  onFollowup,
}: {
  message: ChatMessage;
  onFollowup: (prompt: string) => void;
}) {
  if (message.role === "user") {
    return (
      <article className={styles.userMessage}>
        <p>{message.content}</p>
      </article>
    );
  }

  if (message.error || !message.response) {
    return (
      <article className={`${styles.assistantMessage} ${styles.errorMessage}`}>
        <span className={styles.assistantMark}>K</span>
        <div>
          <strong>Request unavailable</strong>
          <p>{message.content}</p>
        </div>
      </article>
    );
  }

  const { orchestration } = message.response;
  return (
    <article className={styles.assistantMessage}>
      <span className={styles.assistantMark}>K</span>
      <div className={styles.responseBody}>
        <div className={styles.responseHeading}>
          <span>
            <small>Orchestration plan</small>
            <h2>{orchestration.decision_statement}</h2>
          </span>
          <span className={styles.plannedBadge}>Planned</span>
        </div>
        <div className={styles.agentChips}>
          {orchestration.assignments.map((assignment) => (
            <span key={assignment.key}>{assignment.agent}</span>
          ))}
        </div>
        <div className={styles.waveList}>
          {orchestration.execution_waves.map((wave) => (
            <div key={wave.wave}>
              <span>{wave.wave}</span>
              <p>
                <strong>
                  {wave.parallel ? "Parallel specialist analysis" : "Synthesis"}
                </strong>
                {wave.agents
                  .map(
                    (key) =>
                      orchestration.assignments.find(
                        (assignment) => assignment.key === key,
                      )?.agent ?? key,
                  )
                  .join(" · ")}
              </p>
            </div>
          ))}
        </div>
        <div className={styles.responseActions}>
          <button
            type="button"
            onClick={() =>
              onFollowup(
                "Turn this engagement plan into a board-ready presentation with a clear storyline and slide-by-slide structure.",
              )
            }
          >
            <Presentation size={15} />
            Prepare deck
          </button>
          <button
            type="button"
            onClick={() =>
              onFollowup(
                "Create a Mermaid workflow diagram for this engagement plan, including specialist dependencies and review gates.",
              )
            }
          >
            <Network size={15} />
            View workflow
          </button>
        </div>
      </div>
    </article>
  );
}

function ThinkingState() {
  return (
    <article className={styles.assistantMessage}>
      <span className={styles.assistantMark}>K</span>
      <div className={styles.thinking}>
        <span />
        <span />
        <span />
        <p>Orchestrator is preparing the specialist plan</p>
      </div>
    </article>
  );
}

function WorkspacePanel({
  agents,
  artifacts,
  projects,
  view,
  onNewProject,
}: {
  agents: AgentSummary[];
  artifacts: ArtifactSummary[];
  projects: ProjectSummary[];
  view: Exclude<WorkspaceView, "chats">;
  onNewProject: () => void;
}) {
  const titles = {
    projects: ["Projects", "Persistent consulting workspaces"],
    artifacts: ["Artifacts", "Generated presentations, diagrams, and analyses"],
    agents: ["Specialist agents", "The expert team available to the orchestrator"],
  };
  const [title, subtitle] = titles[view];

  return (
    <section className={styles.workspacePanel}>
      <div className={styles.panelHeader}>
        <div>
          <p>KapexAI workspace</p>
          <h1>{title}</h1>
          <span>{subtitle}</span>
        </div>
        {view === "projects" && (
          <button type="button" onClick={onNewProject}>
            <Plus size={16} />
            New project
          </button>
        )}
      </div>

      {view === "projects" && (
        <div className={styles.rowList}>
          {projects.map((project) => (
            <article key={project.id}>
              <span className={styles.rowIcon}>
                <FolderKanban size={19} />
              </span>
              <div>
                <strong>{project.name}</strong>
                <p>{project.description}</p>
              </div>
              <small>{project.company}</small>
            </article>
          ))}
        </div>
      )}

      {view === "artifacts" && (
        <div className={styles.rowList}>
          {artifacts.map((artifact) => (
            <article key={artifact.id}>
              <span className={styles.rowIcon}>
                {artifact.type === "presentation" ? (
                  <Presentation size={19} />
                ) : (
                  <Network size={19} />
                )}
              </span>
              <div>
                <strong>{artifact.name}</strong>
                <p>{artifact.type}</p>
              </div>
              <small>{artifact.updatedAt}</small>
            </article>
          ))}
        </div>
      )}

      {view === "agents" && (
        <div className={styles.agentGrid}>
          {agents.map((agent, index) => (
            <article key={agent.key}>
              <span
                className={styles.agentTileMark}
                style={{
                  backgroundColor:
                    AGENT_ACCENTS[index % AGENT_ACCENTS.length],
                }}
              >
                {agent.name.charAt(0)}
              </span>
              <div>
                <strong>{agent.name}</strong>
                <p>{agent.role}</p>
              </div>
              <small>{agent.deliverables.length} deliverables</small>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
