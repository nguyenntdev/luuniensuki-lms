"use client";

import { useEffect, useMemo, useState } from "react";

import Skeleton from "@/components/Skeleton";
import {
  addClassMember,
  aiGenerateLesson,
  aiGenerateQuiz,
  assignQuestToClass,
  createAdminLesson,
  createAdminQuizQuestion,
  createRagDocument,
  createClass,
  deleteRagDocument,
  getAdminAiJobs,
  getAdminLessons,
  getAdminQuizQuestions,
  getClassDetail,
  getClasses,
  getQuests,
  getRagDocuments,
  getRagSettings,
  rebuildRagEmbeddings,
  removeClassMember,
  updateAdminLesson,
  updateAdminQuizQuestion,
  updateRagDocument,
  updateRagSettings,
  uploadRagDocument,
} from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

const TABS = {
  CONTENT: "content",
  CLASSES: "classes",
  RAG: "rag",
  AI: "ai",
};

const QUESTION_TYPES = [
  "multiple_choice",
  "true_false",
  "image_select",
  "mesh_location",
];
const AI_LEVEL_OPTIONS = [
  { value: "beginner", label: "Cơ bản" },
  { value: "intermediate", label: "Trung bình" },
  { value: "advanced", label: "Nâng cao" },
];

export default function AdminPage() {
  const status = useAuthStore((s) => s.status);
  const user = useAuthStore((s) => s.user);
  const isStaff = ["teacher", "admin", "super_admin"].includes(user?.role);
  const canPublish = ["admin", "super_admin"].includes(user?.role);

  const [activeTab, setActiveTab] = useState(TABS.CONTENT);

  const [motifId, setMotifId] = useState("");
  const [lesson, setLesson] = useState(null);
  const [lessonForm, setLessonForm] = useState({
    intro_text: "",
    description: "",
    historical_context: "",
    symbolism: "",
    fun_fact: "",
    is_published: false,
    is_ai_generated: false,
  });
  const [lessonLoading, setLessonLoading] = useState(false);
  const [lessonError, setLessonError] = useState(null);
  const [lessonNotice, setLessonNotice] = useState(null);

  const [questions, setQuestions] = useState([]);
  const [selectedQuestionId, setSelectedQuestionId] = useState("");
  const [questionForm, setQuestionForm] = useState({
    question_text: "",
    question_type: QUESTION_TYPES[0],
    correct_answer: "",
    options: "[]",
    difficulty: 1,
    explanation: "",
    target_mesh_name: "",
    is_published: false,
    is_active: true,
  });
  const [questionLoading, setQuestionLoading] = useState(false);
  const [questionError, setQuestionError] = useState(null);

  const [classes, setClasses] = useState([]);
  const [classesLoading, setClassesLoading] = useState(false);
  const [classError, setClassError] = useState(null);
  const [className, setClassName] = useState("");
  const [classDescription, setClassDescription] = useState("");
  const [selectedClassId, setSelectedClassId] = useState("");
  const [classDetail, setClassDetail] = useState(null);
  const [memberEmail, setMemberEmail] = useState("");
  const [assignmentQuestId, setAssignmentQuestId] = useState("");
  const [assignmentDueAt, setAssignmentDueAt] = useState("");
  const [quests, setQuests] = useState([]);

  const [ragDocuments, setRagDocuments] = useState([]);
  const [ragLoading, setRagLoading] = useState(false);
  const [ragError, setRagError] = useState(null);
  const [ragNotice, setRagNotice] = useState(null);
  const [ragTitle, setRagTitle] = useState("");
  const [ragContent, setRagContent] = useState("");
  const [ragFile, setRagFile] = useState(null);
  const [selectedRagDocId, setSelectedRagDocId] = useState("");
  const [ragEditForm, setRagEditForm] = useState({
    title: "",
    content: "",
    is_active: true,
  });
  const [ragSettings, setRagSettings] = useState({
    system_instruction: "",
    prompt_prefix: "",
    model_override: "",
    temperature: "",
    max_documents: 6,
    embedding_enabled: true,
    hybrid_alpha: 0.6,
  });
  const [ragEmbeddingNotice, setRagEmbeddingNotice] = useState(null);
  const [aiGenMotifId, setAiGenMotifId] = useState("");
  const [aiGenMotifName, setAiGenMotifName] = useState("");
  const [aiGenUrnSlug, setAiGenUrnSlug] = useState("");
  const [aiGenLevel, setAiGenLevel] = useState("beginner");
  const [aiGenQuizCount, setAiGenQuizCount] = useState(6);
  const [aiGenQuizDifficulty, setAiGenQuizDifficulty] = useState(2);
  const [aiGenForceLesson, setAiGenForceLesson] = useState(false);
  const [aiGenUseSeed, setAiGenUseSeed] = useState(true);
  const [aiGenIncludeQuiz, setAiGenIncludeQuiz] = useState(true);
  const [aiGenReplaceQuiz, setAiGenReplaceQuiz] = useState(false);
  const [aiGenLoading, setAiGenLoading] = useState(false);
  const [aiGenError, setAiGenError] = useState(null);
  const [aiGenNotice, setAiGenNotice] = useState(null);

  const [aiJobs, setAiJobs] = useState([]);
  const [aiJobsLoading, setAiJobsLoading] = useState(false);
  const [aiJobsError, setAiJobsError] = useState(null);
  const [aiJobStatusFilter, setAiJobStatusFilter] = useState("");
  const [aiJobTypeFilter, setAiJobTypeFilter] = useState("");

  useEffect(() => {
    if (!isStaff || status !== "authed") return;
    let cancelled = false;

    async function loadClasses() {
      setClassesLoading(true);
      setClassError(null);
      try {
        const res = await getClasses();
        if (cancelled) return;
        setClasses(Array.isArray(res) ? res : []);
      } catch (err) {
        if (!cancelled)
          setClassError(err instanceof Error ? err.message : String(err));
      } finally {
        if (!cancelled) setClassesLoading(false);
      }
    }

    async function loadQuests() {
      try {
        const res = await getQuests();
        if (!cancelled) setQuests(Array.isArray(res) ? res : []);
      } catch {
        if (!cancelled) setQuests([]);
      }
    }

    loadClasses();
    loadQuests();
    return () => {
      cancelled = true;
    };
  }, [isStaff, status]);

  useEffect(() => {
    if (!isStaff || status !== "authed" || activeTab !== TABS.RAG) return;
    let cancelled = false;

    async function loadRagResources() {
      setRagLoading(true);
      setRagError(null);
      setRagNotice(null);
      try {
        const [docsRes, settingsRes] = await Promise.allSettled([
          getRagDocuments(),
          getRagSettings(),
        ]);

        if (!cancelled && docsRes.status === "fulfilled") {
          setRagDocuments(Array.isArray(docsRes.value) ? docsRes.value : []);
        }

        if (!cancelled && settingsRes.status === "fulfilled") {
          const data = settingsRes.value || {};
          setRagSettings({
            system_instruction: data.system_instruction || "",
            prompt_prefix: data.prompt_prefix || "",
            model_override: data.model_override || "",
            temperature:
              data.temperature === null || data.temperature === undefined
                ? ""
                : String(data.temperature),
            max_documents:
              typeof data.max_documents === "number" ? data.max_documents : 6,
            embedding_enabled: data.embedding_enabled ?? true,
            hybrid_alpha:
              typeof data.hybrid_alpha === "number" ? data.hybrid_alpha : 0.6,
          });
        }
      } catch (err) {
        if (!cancelled) {
          setRagError(err instanceof Error ? err.message : String(err));
        }
      } finally {
        if (!cancelled) setRagLoading(false);
      }
    }

    loadRagResources();
    return () => {
      cancelled = true;
    };
  }, [activeTab, isStaff, status]);

  useEffect(() => {
    if (!isStaff || status !== "authed" || activeTab !== TABS.AI) return;
    let cancelled = false;

    async function loadJobs() {
      setAiJobsLoading(true);
      setAiJobsError(null);
      try {
        const res = await getAdminAiJobs({
          status: aiJobStatusFilter || undefined,
          jobType: aiJobTypeFilter || undefined,
          limit: 100,
        });
        if (!cancelled) setAiJobs(Array.isArray(res) ? res : []);
      } catch (err) {
        if (!cancelled)
          setAiJobsError(err instanceof Error ? err.message : String(err));
      } finally {
        if (!cancelled) setAiJobsLoading(false);
      }
    }

    loadJobs();
    return () => {
      cancelled = true;
    };
  }, [activeTab, aiJobStatusFilter, aiJobTypeFilter, isStaff, status]);

  const selectedQuestion = useMemo(() => {
    return questions.find((q) => q.id === selectedQuestionId) || null;
  }, [questions, selectedQuestionId]);

  const selectedRagDoc = useMemo(() => {
    return ragDocuments.find((doc) => doc.id === selectedRagDocId) || null;
  }, [ragDocuments, selectedRagDocId]);

  const classSummary = useMemo(() => {
    if (!classDetail) return null;
    const members = Array.isArray(classDetail.members)
      ? classDetail.members
      : [];
    const assignments = Array.isArray(classDetail.assignments)
      ? classDetail.assignments
      : [];
    const assignmentCount = assignments.length;
    const completionPercent = assignmentCount
      ? Math.round(
          assignments.reduce(
            (total, assignment) =>
              total + (Number(assignment.completion_percent) || 0),
            0,
          ) / assignmentCount,
        )
      : 0;
    return {
      memberCount: members.length,
      assignmentCount,
      completionPercent,
    };
  }, [classDetail]);

  useEffect(() => {
    if (!selectedQuestion) return;
    setQuestionForm({
      question_text: selectedQuestion.question_text || "",
      question_type: selectedQuestion.question_type || QUESTION_TYPES[0],
      correct_answer: selectedQuestion.correct_answer || "",
      options: JSON.stringify(selectedQuestion.options || [], null, 2),
      difficulty: selectedQuestion.difficulty || 1,
      explanation: selectedQuestion.explanation || "",
      target_mesh_name: selectedQuestion.target_mesh_name || "",
      is_published: Boolean(selectedQuestion.is_published),
      is_active: Boolean(selectedQuestion.is_active),
    });
  }, [selectedQuestion]);

  useEffect(() => {
    if (!selectedRagDoc) return;
    setRagEditForm({
      title: selectedRagDoc.title || "",
      content: selectedRagDoc.content || "",
      is_active: selectedRagDoc.is_active !== false,
    });
  }, [selectedRagDoc]);

  async function handleLoadContent() {
    if (!motifId) return;
    setLessonLoading(true);
    setQuestionLoading(true);
    setLessonError(null);
    setQuestionError(null);
    setLessonNotice(null);
    try {
      const [lessonRes, questionRes] = await Promise.allSettled([
        getAdminLessons({ motifId }),
        getAdminQuizQuestions({ motifId }),
      ]);

      if (lessonRes.status === "fulfilled") {
        const data = lessonRes.value?.[0] || null;
        setLesson(data);
        if (data) {
          setLessonForm({
            intro_text: data.intro_text || "",
            description: data.description || "",
            historical_context: data.historical_context || "",
            symbolism: data.symbolism || "",
            fun_fact: data.fun_fact || "",
            is_published: Boolean(data.is_published),
            is_ai_generated: Boolean(data.is_ai_generated),
          });
        } else {
          setLessonForm((prev) => ({
            ...prev,
            description: "",
            intro_text: "",
            historical_context: "",
            symbolism: "",
            fun_fact: "",
            is_published: false,
          }));
          setLessonNotice("Chưa có bài học, hãy tạo mới.");
        }
      } else {
        setLessonError("Không thể tải bài học.");
      }

      if (questionRes.status === "fulfilled") {
        setQuestions(Array.isArray(questionRes.value) ? questionRes.value : []);
        setSelectedQuestionId("");
      } else {
        setQuestionError("Không thể tải câu hỏi.");
      }
    } catch (err) {
      setLessonError(err instanceof Error ? err.message : String(err));
    } finally {
      setLessonLoading(false);
      setQuestionLoading(false);
    }
  }

  async function handleSaveLesson() {
    if (!motifId) return;
    setLessonLoading(true);
    setLessonError(null);
    setLessonNotice(null);
    try {
      const payload = {
        motif_id: motifId,
        ...lessonForm,
        is_published: canPublish ? lessonForm.is_published : false,
      };
      let res;
      if (lesson?.id) {
        res = await updateAdminLesson({
          lessonId: lesson.id,
          ...payload,
        });
      } else {
        res = await createAdminLesson(payload);
      }
      setLesson(res || null);
      setLessonNotice("Đã lưu bài học.");
    } catch (err) {
      setLessonError(err instanceof Error ? err.message : String(err));
    } finally {
      setLessonLoading(false);
    }
  }

  async function handleSaveQuestion() {
    if (!motifId) return;
    setQuestionLoading(true);
    setQuestionError(null);
    try {
      let options = [];
      if (questionForm.options?.trim()) {
        options = JSON.parse(questionForm.options);
      }
      const payload = {
        motif_id: motifId,
        question_text: questionForm.question_text,
        question_type: questionForm.question_type,
        correct_answer: questionForm.correct_answer,
        options,
        difficulty: Number(questionForm.difficulty || 1),
        explanation: questionForm.explanation || null,
        target_mesh_name: questionForm.target_mesh_name || null,
        is_published: canPublish ? questionForm.is_published : false,
        is_active: Boolean(questionForm.is_active),
      };
      let res;
      if (selectedQuestionId) {
        res = await updateAdminQuizQuestion({
          questionId: selectedQuestionId,
          ...payload,
        });
      } else {
        res = await createAdminQuizQuestion(payload);
      }
      setQuestions((prev) => {
        const filtered = prev.filter((q) => q.id !== res.id);
        return [res, ...filtered];
      });
      setSelectedQuestionId(res.id);
    } catch (err) {
      setQuestionError(err instanceof Error ? err.message : String(err));
    } finally {
      setQuestionLoading(false);
    }
  }

  async function handleCreateClass() {
    if (!className.trim()) return;
    setClassError(null);
    try {
      const res = await createClass({
        name: className.trim(),
        description: classDescription.trim() || null,
      });
      setClasses((prev) => [res, ...prev]);
      setClassName("");
      setClassDescription("");
    } catch (err) {
      setClassError(err instanceof Error ? err.message : String(err));
    }
  }

  async function handleSelectClass(classId) {
    setSelectedClassId(classId);
    setClassDetail(null);
    setClassError(null);
    try {
      const res = await getClassDetail({ classId });
      setClassDetail(res || null);
    } catch (err) {
      setClassError(err instanceof Error ? err.message : String(err));
    }
  }

  async function handleAddMember() {
    if (!selectedClassId || !memberEmail.trim()) return;
    setClassError(null);
    try {
      const res = await addClassMember({
        classId: selectedClassId,
        email: memberEmail.trim(),
      });
      setClassDetail(res || null);
      setMemberEmail("");
    } catch (err) {
      setClassError(err instanceof Error ? err.message : String(err));
    }
  }

  async function handleRemoveMember(userId) {
    if (!selectedClassId || !userId) return;
    setClassError(null);
    try {
      const res = await removeClassMember({
        classId: selectedClassId,
        userId,
      });
      setClassDetail(res || null);
    } catch (err) {
      setClassError(err instanceof Error ? err.message : String(err));
    }
  }

  async function handleAssignQuest() {
    if (!selectedClassId || !assignmentQuestId) return;
    setClassError(null);
    try {
      const dueAtIso = assignmentDueAt
        ? new Date(assignmentDueAt).toISOString()
        : null;
      const res = await assignQuestToClass({
        classId: selectedClassId,
        questId: assignmentQuestId,
        dueAt: dueAtIso,
      });
      setClassDetail(res || null);
      setAssignmentQuestId("");
      setAssignmentDueAt("");
    } catch (err) {
      setClassError(err instanceof Error ? err.message : String(err));
    }
  }

  async function handleSaveRagSettings() {
    setRagError(null);
    setRagNotice(null);
    setRagEmbeddingNotice(null);
    try {
      const payload = {
        system_instruction: ragSettings.system_instruction || null,
        prompt_prefix: ragSettings.prompt_prefix || null,
        model_override: ragSettings.model_override || null,
        temperature:
          ragSettings.temperature === ""
            ? null
            : Number(ragSettings.temperature),
        max_documents: Number(ragSettings.max_documents || 6),
        embedding_enabled: Boolean(ragSettings.embedding_enabled),
        hybrid_alpha: Number(ragSettings.hybrid_alpha ?? 0.6),
      };
      const res = await updateRagSettings(payload);
      setRagSettings({
        system_instruction: res.system_instruction || "",
        prompt_prefix: res.prompt_prefix || "",
        model_override: res.model_override || "",
        temperature:
          res.temperature === null || res.temperature === undefined
            ? ""
            : String(res.temperature),
        max_documents:
          typeof res.max_documents === "number" ? res.max_documents : 6,
        embedding_enabled: res.embedding_enabled ?? true,
        hybrid_alpha:
          typeof res.hybrid_alpha === "number" ? res.hybrid_alpha : 0.6,
      });
      setRagNotice("Đã lưu cấu hình AI.");
    } catch (err) {
      setRagError(err instanceof Error ? err.message : String(err));
    }
  }

  async function handleRebuildEmbeddings() {
    setRagError(null);
    setRagEmbeddingNotice(null);
    try {
      const res = await rebuildRagEmbeddings();
      setRagEmbeddingNotice(
        `Đã cập nhật embedding: ${res.updated}/${res.total} tài liệu.`,
      );
      const docsRes = await getRagDocuments();
      setRagDocuments(Array.isArray(docsRes) ? docsRes : []);
    } catch (err) {
      setRagError(err instanceof Error ? err.message : String(err));
    }
  }

  async function handleRefreshAiJobs() {
    setAiJobsLoading(true);
    setAiJobsError(null);
    try {
      const res = await getAdminAiJobs({
        status: aiJobStatusFilter || undefined,
        jobType: aiJobTypeFilter || undefined,
        limit: 100,
      });
      setAiJobs(Array.isArray(res) ? res : []);
    } catch (err) {
      setAiJobsError(err instanceof Error ? err.message : String(err));
    } finally {
      setAiJobsLoading(false);
    }
  }

  async function handleCreateRagDocument() {
    if (!ragTitle || !ragContent) return;
    setRagError(null);
    setRagNotice(null);
    try {
      const res = await createRagDocument({
        title: ragTitle,
        content: ragContent,
        is_active: true,
      });
      setRagDocuments((prev) => [res, ...prev]);
      setRagTitle("");
      setRagContent("");
      setRagNotice("Đã thêm tài liệu.");
    } catch (err) {
      setRagError(err instanceof Error ? err.message : String(err));
    }
  }

  async function handleUploadRagFile() {
    if (!ragFile) return;
    setRagError(null);
    setRagNotice(null);
    try {
      const res = await uploadRagDocument({
        file: ragFile,
        title: ragTitle || undefined,
      });
      setRagDocuments((prev) => [res, ...prev]);
      setRagFile(null);
      setRagTitle("");
      setRagNotice("Đã tải file vào RAG.");
    } catch (err) {
      setRagError(err instanceof Error ? err.message : String(err));
    }
  }

  async function handleUpdateRagDocument() {
    if (!selectedRagDocId) return;
    setRagError(null);
    setRagNotice(null);
    try {
      const res = await updateRagDocument({
        docId: selectedRagDocId,
        title: ragEditForm.title,
        content: ragEditForm.content,
        is_active: ragEditForm.is_active,
      });
      setRagDocuments((prev) =>
        prev.map((doc) => (doc.id === res.id ? res : doc)),
      );
      setRagNotice("Đã cập nhật tài liệu.");
    } catch (err) {
      setRagError(err instanceof Error ? err.message : String(err));
    }
  }

  async function handleDeleteRagDocument(docId) {
    setRagError(null);
    setRagNotice(null);
    try {
      await deleteRagDocument({ docId });
      setRagDocuments((prev) => prev.filter((doc) => doc.id !== docId));
      if (selectedRagDocId === docId) {
        setSelectedRagDocId("");
        setRagEditForm({ title: "", content: "", is_active: true });
      }
      setRagNotice("Đã xoá tài liệu.");
    } catch (err) {
      setRagError(err instanceof Error ? err.message : String(err));
    }
  }

  async function handleGenerateLesson() {
    setAiGenError(null);
    setAiGenNotice(null);
    if (!aiGenMotifId && !aiGenMotifName) {
      setAiGenError("Nhập motif ID hoặc tên họa tiết.");
      return;
    }
    setAiGenLoading(true);
    try {
      const res = await aiGenerateLesson({
        motif_id: aiGenMotifId || undefined,
        motif_name: aiGenMotifName || undefined,
        urn_slug: aiGenUrnSlug || undefined,
        level: aiGenLevel,
        language: "vi",
        force: aiGenForceLesson,
        use_seed: aiGenUseSeed,
        generate_quiz: aiGenIncludeQuiz,
        quiz_count: Number(aiGenQuizCount) || 6,
      });
      setAiGenNotice(
        `Đã tạo bài học: ${res.summary || "Hoàn tất"} (motif ${res.motif_id}).`,
      );
    } catch (err) {
      setAiGenError(err instanceof Error ? err.message : String(err));
    } finally {
      setAiGenLoading(false);
    }
  }

  async function handleGenerateQuiz() {
    setAiGenError(null);
    setAiGenNotice(null);
    if (!aiGenMotifId && !aiGenMotifName) {
      setAiGenError("Nhập motif ID hoặc tên họa tiết.");
      return;
    }
    setAiGenLoading(true);
    try {
      const res = await aiGenerateQuiz({
        motif_id: aiGenMotifId || undefined,
        motif_name: aiGenMotifName || undefined,
        urn_slug: aiGenUrnSlug || undefined,
        count: Number(aiGenQuizCount) || 6,
        difficulty: Number(aiGenQuizDifficulty) || 2,
        replace_existing: aiGenReplaceQuiz,
        use_seed: aiGenUseSeed,
      });
      setAiGenNotice(`Đã tạo ${res.question_ids?.length || 0} câu hỏi quiz.`);
    } catch (err) {
      setAiGenError(err instanceof Error ? err.message : String(err));
    } finally {
      setAiGenLoading(false);
    }
  }

  if (status !== "authed") {
    return (
      <main className="mx-auto max-w-4xl px-6 py-10">
        <div className="rounded-xl border border-border bg-card p-6">
          <h1 className="text-xl font-display font-semibold">Teacher Hub</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Vui lòng đăng nhập để tiếp tục.
          </p>
        </div>
      </main>
    );
  }

  if (!isStaff) {
    return (
      <main className="mx-auto max-w-4xl px-6 py-10">
        <div className="rounded-xl border border-border bg-card p-6">
          <h1 className="text-xl font-display font-semibold">Teacher Hub</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Bạn không có quyền truy cập trang này.
          </p>
        </div>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-6xl px-6 py-10 pb-24">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-display font-bold text-foreground">
            Teacher Hub
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Quản lý nội dung, lớp học và bài tập quest.
          </p>
        </div>
      </div>

      <div className="mt-6 rounded-2xl border border-border bg-card p-2">
        <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
          <button
            type="button"
            onClick={() => setActiveTab(TABS.CONTENT)}
            className={[
              "rounded-xl px-4 py-2 text-sm font-semibold transition",
              activeTab === TABS.CONTENT
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:bg-muted hover:text-foreground",
            ].join(" ")}
          >
            Nội dung
          </button>
          <button
            type="button"
            onClick={() => setActiveTab(TABS.CLASSES)}
            className={[
              "rounded-xl px-4 py-2 text-sm font-semibold transition",
              activeTab === TABS.CLASSES
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:bg-muted hover:text-foreground",
            ].join(" ")}
          >
            Lớp học
          </button>
          <button
            type="button"
            onClick={() => setActiveTab(TABS.RAG)}
            className={[
              "rounded-xl px-4 py-2 text-sm font-semibold transition",
              activeTab === TABS.RAG
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:bg-muted hover:text-foreground",
            ].join(" ")}
          >
            AI / RAG
          </button>
          <button
            type="button"
            onClick={() => setActiveTab(TABS.AI)}
            className={[
              "rounded-xl px-4 py-2 text-sm font-semibold transition",
              activeTab === TABS.AI
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:bg-muted hover:text-foreground",
            ].join(" ")}
          >
            AI History
          </button>
        </div>
      </div>

      {activeTab === TABS.CONTENT ? (
        <section className="mt-8 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
            <h2 className="text-lg font-display font-semibold text-foreground">
              Bài học
            </h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Nhập motif ID để chỉnh sửa hoặc tạo mới bài học.
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              <input
                type="text"
                value={motifId}
                onChange={(e) => setMotifId(e.target.value)}
                placeholder="Motif ID..."
                className="flex-1 rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
              />
              <button
                type="button"
                onClick={handleLoadContent}
                className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
              >
                Tải nội dung
              </button>
            </div>

            {lessonError ? (
              <div className="mt-4 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
                {lessonError}
              </div>
            ) : null}
            {lessonNotice ? (
              <div className="mt-4 rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3 text-sm text-emerald-700">
                {lessonNotice}
              </div>
            ) : null}

            {lessonLoading ? (
              <div className="mt-6 space-y-3">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-4 w-full" />
              </div>
            ) : (
              <div className="mt-6 space-y-4">
                <div>
                  <label className="text-xs font-medium text-muted-foreground">
                    Intro
                  </label>
                  <input
                    type="text"
                    value={lessonForm.intro_text}
                    onChange={(e) =>
                      setLessonForm((prev) => ({
                        ...prev,
                        intro_text: e.target.value,
                      }))
                    }
                    className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground">
                    Nội dung
                  </label>
                  <textarea
                    rows={6}
                    value={lessonForm.description}
                    onChange={(e) =>
                      setLessonForm((prev) => ({
                        ...prev,
                        description: e.target.value,
                      }))
                    }
                    className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
                  />
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">
                      Bối cảnh lịch sử
                    </label>
                    <input
                      type="text"
                      value={lessonForm.historical_context}
                      onChange={(e) =>
                        setLessonForm((prev) => ({
                          ...prev,
                          historical_context: e.target.value,
                        }))
                      }
                      className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">
                      Biểu tượng
                    </label>
                    <input
                      type="text"
                      value={lessonForm.symbolism}
                      onChange={(e) =>
                        setLessonForm((prev) => ({
                          ...prev,
                          symbolism: e.target.value,
                        }))
                      }
                      className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
                    />
                  </div>
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground">
                    Fun fact
                  </label>
                  <input
                    type="text"
                    value={lessonForm.fun_fact}
                    onChange={(e) =>
                      setLessonForm((prev) => ({
                        ...prev,
                        fun_fact: e.target.value,
                      }))
                    }
                    className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
                  />
                </div>
                <div className="flex flex-wrap gap-4">
                  <label className="flex items-center gap-2 text-sm text-foreground">
                    <input
                      type="checkbox"
                      checked={lessonForm.is_ai_generated}
                      onChange={(e) =>
                        setLessonForm((prev) => ({
                          ...prev,
                          is_ai_generated: e.target.checked,
                        }))
                      }
                      className="h-4 w-4 rounded border-border text-primary focus:ring-primary"
                    />
                    AI nội dung
                  </label>
                  <label className="flex items-center gap-2 text-sm text-foreground">
                    <input
                      type="checkbox"
                      checked={lessonForm.is_published}
                      disabled={!canPublish}
                      onChange={(e) =>
                        setLessonForm((prev) => ({
                          ...prev,
                          is_published: e.target.checked,
                        }))
                      }
                      className="h-4 w-4 rounded border-border text-primary focus:ring-primary disabled:opacity-60"
                    />
                    Xuất bản
                  </label>
                </div>
                <button
                  type="button"
                  onClick={handleSaveLesson}
                  disabled={lessonLoading}
                  className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
                >
                  {lesson ? "Lưu thay đổi" : "Tạo bài học"}
                </button>
              </div>
            )}
          </div>

          <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
            <h2 className="text-lg font-display font-semibold text-foreground">
              Quiz Questions
            </h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Quản lý câu hỏi cho motif.
            </p>

            {questionError ? (
              <div className="mt-4 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
                {questionError}
              </div>
            ) : null}

            {questionLoading ? (
              <div className="mt-4 space-y-3">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-4 w-full" />
              </div>
            ) : (
              <>
                <div className="mt-4 space-y-2">
                  {questions.length ? (
                    questions.map((q) => (
                      <button
                        key={q.id}
                        type="button"
                        onClick={() => setSelectedQuestionId(q.id)}
                        className={[
                          "w-full rounded-lg border px-3 py-2 text-left text-sm",
                          selectedQuestionId === q.id
                            ? "border-primary bg-primary/10"
                            : "border-border hover:bg-muted",
                        ].join(" ")}
                      >
                        <div className="font-semibold text-foreground">
                          {q.question_text}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {q.question_type} ·{" "}
                          {q.is_published ? "Đã xuất bản" : "Nháp"}
                        </div>
                      </button>
                    ))
                  ) : (
                    <div className="text-sm text-muted-foreground">
                      Chưa có câu hỏi nào.
                    </div>
                  )}
                </div>

                <div className="mt-6 space-y-3">
                  <input
                    type="text"
                    value={questionForm.question_text}
                    onChange={(e) =>
                      setQuestionForm((prev) => ({
                        ...prev,
                        question_text: e.target.value,
                      }))
                    }
                    placeholder="Nội dung câu hỏi"
                    className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
                  />
                  <div className="grid gap-3 sm:grid-cols-2">
                    <select
                      value={questionForm.question_type}
                      onChange={(e) =>
                        setQuestionForm((prev) => ({
                          ...prev,
                          question_type: e.target.value,
                        }))
                      }
                      className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
                    >
                      {QUESTION_TYPES.map((type) => (
                        <option key={type} value={type}>
                          {type}
                        </option>
                      ))}
                    </select>
                    <input
                      type="text"
                      value={questionForm.correct_answer}
                      onChange={(e) =>
                        setQuestionForm((prev) => ({
                          ...prev,
                          correct_answer: e.target.value,
                        }))
                      }
                      placeholder="Đáp án đúng"
                      className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
                    />
                  </div>
                  <textarea
                    rows={3}
                    value={questionForm.options}
                    onChange={(e) =>
                      setQuestionForm((prev) => ({
                        ...prev,
                        options: e.target.value,
                      }))
                    }
                    placeholder='Options JSON: ["A", "B"]'
                    className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
                  />
                  <input
                    type="number"
                    min="1"
                    max="5"
                    value={questionForm.difficulty}
                    onChange={(e) =>
                      setQuestionForm((prev) => ({
                        ...prev,
                        difficulty: e.target.value,
                      }))
                    }
                    placeholder="Độ khó (1-5)"
                    className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
                  />
                  <input
                    type="text"
                    value={questionForm.target_mesh_name}
                    onChange={(e) =>
                      setQuestionForm((prev) => ({
                        ...prev,
                        target_mesh_name: e.target.value,
                      }))
                    }
                    placeholder="Target mesh name (optional)"
                    className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
                  />
                  <textarea
                    rows={2}
                    value={questionForm.explanation}
                    onChange={(e) =>
                      setQuestionForm((prev) => ({
                        ...prev,
                        explanation: e.target.value,
                      }))
                    }
                    placeholder="Giải thích"
                    className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
                  />
                  <div className="flex flex-wrap gap-4">
                    <label className="flex items-center gap-2 text-sm text-foreground">
                      <input
                        type="checkbox"
                        checked={questionForm.is_published}
                        disabled={!canPublish}
                        onChange={(e) =>
                          setQuestionForm((prev) => ({
                            ...prev,
                            is_published: e.target.checked,
                          }))
                        }
                        className="h-4 w-4 rounded border-border text-primary focus:ring-primary disabled:opacity-60"
                      />
                      Xuất bản
                    </label>
                    <label className="flex items-center gap-2 text-sm text-foreground">
                      <input
                        type="checkbox"
                        checked={questionForm.is_active}
                        onChange={(e) =>
                          setQuestionForm((prev) => ({
                            ...prev,
                            is_active: e.target.checked,
                          }))
                        }
                        className="h-4 w-4 rounded border-border text-primary focus:ring-primary"
                      />
                      Kích hoạt
                    </label>
                  </div>
                  <button
                    type="button"
                    onClick={handleSaveQuestion}
                    disabled={questionLoading}
                    className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
                  >
                    {selectedQuestionId ? "Lưu câu hỏi" : "Tạo câu hỏi"}
                  </button>
                </div>
              </>
            )}
          </div>
        </section>
      ) : activeTab === TABS.CLASSES ? (
        <section className="mt-8 grid gap-6 lg:grid-cols-[1fr_1.2fr]">
          <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
            <h2 className="text-lg font-display font-semibold text-foreground">
              Lớp học
            </h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Tạo lớp mới và chọn lớp để quản lý.
            </p>

            <div className="mt-4 space-y-3">
              <input
                type="text"
                value={className}
                onChange={(e) => setClassName(e.target.value)}
                placeholder="Tên lớp"
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
              />
              <textarea
                rows={3}
                value={classDescription}
                onChange={(e) => setClassDescription(e.target.value)}
                placeholder="Mô tả lớp"
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
              />
              <button
                type="button"
                onClick={handleCreateClass}
                className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
              >
                Tạo lớp
              </button>
            </div>

            {classesLoading ? (
              <div className="mt-6 space-y-2">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-4 w-2/3" />
              </div>
            ) : (
              <div className="mt-6 space-y-2">
                {classes.map((cls) => (
                  <button
                    key={cls.id}
                    type="button"
                    onClick={() => handleSelectClass(cls.id)}
                    className={[
                      "w-full rounded-lg border px-3 py-2 text-left text-sm",
                      selectedClassId === cls.id
                        ? "border-primary bg-primary/10"
                        : "border-border hover:bg-muted",
                    ].join(" ")}
                  >
                    <div className="font-semibold text-foreground">
                      {cls.name}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {cls.member_count} học viên · {cls.assignment_count} bài
                      tập
                    </div>
                  </button>
                ))}
                {!classes.length ? (
                  <div className="text-sm text-muted-foreground">
                    Chưa có lớp nào.
                  </div>
                ) : null}
              </div>
            )}
          </div>

          <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
            <h2 className="text-lg font-display font-semibold text-foreground">
              Quản lý lớp
            </h2>
            {classError ? (
              <div className="mt-4 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
                {classError}
              </div>
            ) : null}

            {selectedClassId && classDetail ? (
              <div className="mt-4 space-y-6">
                {classSummary ? (
                  <div className="rounded-xl border border-border bg-secondary/30 p-4">
                    <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                      Tiến độ lớp
                    </div>
                    <div className="mt-2 text-2xl font-display font-bold text-foreground">
                      {classSummary.completionPercent}%
                    </div>
                    <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-muted">
                      <div
                        className="h-full bg-primary"
                        style={{
                          width: `${classSummary.completionPercent}%`,
                        }}
                      />
                    </div>
                    <div className="mt-2 text-xs text-muted-foreground">
                      {classSummary.memberCount} học viên ·{" "}
                      {classSummary.assignmentCount} bài tập
                    </div>
                  </div>
                ) : null}
                <div>
                  <h3 className="text-sm font-semibold text-foreground">
                    Thành viên
                  </h3>
                  <div className="mt-2 flex gap-2">
                    <input
                      type="email"
                      value={memberEmail}
                      onChange={(e) => setMemberEmail(e.target.value)}
                      placeholder="Email học viên"
                      className="flex-1 rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
                    />
                    <button
                      type="button"
                      onClick={handleAddMember}
                      className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
                    >
                      Thêm
                    </button>
                  </div>
                  <div className="mt-3 space-y-2">
                    {classDetail.members.map((member) => (
                      <div
                        key={member.user_id}
                        className="flex items-center justify-between rounded-lg border border-border bg-secondary/40 px-3 py-2 text-sm"
                      >
                        <div>
                          <div className="font-semibold text-foreground">
                            {member.display_name}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {member.email}
                          </div>
                        </div>
                        <button
                          type="button"
                          onClick={() => handleRemoveMember(member.user_id)}
                          className="text-xs font-semibold text-destructive hover:text-destructive/80"
                        >
                          Xóa
                        </button>
                      </div>
                    ))}
                    {!classDetail.members.length ? (
                      <div className="text-sm text-muted-foreground">
                        Chưa có học viên.
                      </div>
                    ) : null}
                  </div>
                </div>

                <div>
                  <h3 className="text-sm font-semibold text-foreground">
                    Giao quest
                  </h3>
                  <div className="mt-2 grid gap-2 sm:grid-cols-[1fr_1fr_auto]">
                    <select
                      value={assignmentQuestId}
                      onChange={(e) => setAssignmentQuestId(e.target.value)}
                      className="rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
                    >
                      <option value="">Chọn quest</option>
                      {quests.map((quest) => (
                        <option key={quest.id} value={quest.id}>
                          {quest.name}
                        </option>
                      ))}
                    </select>
                    <input
                      type="date"
                      value={assignmentDueAt}
                      onChange={(e) => setAssignmentDueAt(e.target.value)}
                      className="rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
                    />
                    <button
                      type="button"
                      onClick={handleAssignQuest}
                      className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
                    >
                      Giao
                    </button>
                  </div>
                  <div className="mt-3 space-y-2">
                    {classDetail.assignments.map((assignment) => (
                      <div
                        key={assignment.id}
                        className="rounded-lg border border-border bg-secondary/40 px-3 py-2 text-sm"
                      >
                        <div className="font-semibold text-foreground">
                          {assignment.quest_name}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          Hoàn thành:{" "}
                          {Math.round(assignment.completion_percent || 0)}%
                        </div>
                      </div>
                    ))}
                    {!classDetail.assignments.length ? (
                      <div className="text-sm text-muted-foreground">
                        Chưa có bài tập.
                      </div>
                    ) : null}
                  </div>
                </div>
              </div>
            ) : (
              <div className="mt-4 text-sm text-muted-foreground">
                Chọn lớp để xem chi tiết.
              </div>
            )}
          </div>
        </section>
      ) : activeTab === TABS.AI ? (
        <section className="mt-8 space-y-6">
          <div className="rounded-2xl border border-border bg-card p-6 shadow-sm space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-display font-semibold text-foreground">
                  AI history
                </h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  Theo dõi prompt/response gần đây để kiểm soát chất lượng.
                </p>
              </div>
              <button
                type="button"
                onClick={handleRefreshAiJobs}
                className="rounded-lg border border-border px-4 py-2 text-sm font-semibold text-foreground hover:bg-muted"
              >
                Làm mới
              </button>
            </div>

            <div className="grid gap-3 sm:grid-cols-[1fr_1fr_auto]">
              <select
                value={aiJobStatusFilter}
                onChange={(e) => setAiJobStatusFilter(e.target.value)}
                className="rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
              >
                <option value="">Tất cả trạng thái</option>
                <option value="pending">Pending</option>
                <option value="succeeded">Succeeded</option>
                <option value="failed">Failed</option>
              </select>
              <input
                type="text"
                value={aiJobTypeFilter}
                onChange={(e) => setAiJobTypeFilter(e.target.value)}
                placeholder="Lọc theo job type (tutor, qa, ...)"
                className="rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
              />
              <button
                type="button"
                onClick={() => {
                  setAiJobStatusFilter("");
                  setAiJobTypeFilter("");
                }}
                className="rounded-lg border border-border px-3 py-2 text-sm font-semibold text-foreground hover:bg-muted"
              >
                Reset
              </button>
            </div>

            {aiJobsError ? (
              <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
                {aiJobsError}
              </div>
            ) : null}

            {aiJobsLoading ? (
              <div className="space-y-2">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-4 w-2/3" />
                <Skeleton className="h-4 w-1/2" />
              </div>
            ) : (
              <div className="max-h-[420px] space-y-3 overflow-auto pr-1">
                {aiJobs.map((job) => (
                  <details
                    key={job.id}
                    className="rounded-xl border border-border bg-background/60 p-4"
                  >
                    <summary className="cursor-pointer list-none">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div>
                          <div className="text-sm font-semibold text-foreground">
                            {job.job_type} · {job.status}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {job.user_email || job.user_id} ·{" "}
                            {new Date(job.created_at).toLocaleString("vi-VN")}
                          </div>
                        </div>
                        <span className="rounded-full border border-border px-3 py-1 text-xs font-semibold text-muted-foreground">
                          {job.provider || "ai"} · retry {job.retry_count}
                        </span>
                      </div>
                    </summary>
                    <div className="mt-3 space-y-2 text-xs text-muted-foreground">
                      {job.prompt ? (
                        <div>
                          <div className="font-semibold text-foreground">
                            Prompt
                          </div>
                          <pre className="mt-1 whitespace-pre-wrap rounded-lg bg-muted/40 p-3 text-xs text-foreground">
                            {job.prompt}
                          </pre>
                        </div>
                      ) : null}
                      {job.response ? (
                        <div>
                          <div className="font-semibold text-foreground">
                            Response
                          </div>
                          <pre className="mt-1 whitespace-pre-wrap rounded-lg bg-muted/40 p-3 text-xs text-foreground">
                            {job.response}
                          </pre>
                        </div>
                      ) : null}
                      {job.error ? (
                        <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-xs text-destructive">
                          {job.error}
                        </div>
                      ) : null}
                    </div>
                  </details>
                ))}
                {!aiJobs.length ? (
                  <div className="text-sm text-muted-foreground">
                    Chưa có log AI.
                  </div>
                ) : null}
              </div>
            )}
          </div>
        </section>
      ) : (
        <section className="mt-8 grid gap-6 lg:grid-cols-[1fr_1fr]">
          <div className="rounded-2xl border border-border bg-card p-6 shadow-sm space-y-6">
            <div>
              <h2 className="text-lg font-display font-semibold text-foreground">
                Cấu hình AI
              </h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Thiết lập hệ thống prompt, model và số tài liệu dùng cho RAG.
              </p>
            </div>

            {ragError ? (
              <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
                {ragError}
              </div>
            ) : null}
            {ragNotice ? (
              <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3 text-sm text-emerald-700">
                {ragNotice}
              </div>
            ) : null}
            {ragEmbeddingNotice ? (
              <div className="rounded-lg border border-sky-500/30 bg-sky-500/10 p-3 text-sm text-sky-700">
                {ragEmbeddingNotice}
              </div>
            ) : null}

            <div className="space-y-4">
              <div>
                <label className="text-xs font-medium text-muted-foreground">
                  System instruction
                </label>
                <textarea
                  rows={3}
                  value={ragSettings.system_instruction}
                  onChange={(e) =>
                    setRagSettings((prev) => ({
                      ...prev,
                      system_instruction: e.target.value,
                    }))
                  }
                  className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground">
                  Prompt prefix
                </label>
                <textarea
                  rows={3}
                  value={ragSettings.prompt_prefix}
                  onChange={(e) =>
                    setRagSettings((prev) => ({
                      ...prev,
                      prompt_prefix: e.target.value,
                    }))
                  }
                  className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
                />
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <div>
                  <label className="text-xs font-medium text-muted-foreground">
                    Model override
                  </label>
                  <input
                    type="text"
                    value={ragSettings.model_override}
                    onChange={(e) =>
                      setRagSettings((prev) => ({
                        ...prev,
                        model_override: e.target.value,
                      }))
                    }
                    placeholder="deepseek-v3"
                    className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground">
                    Temperature
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="2"
                    value={ragSettings.temperature}
                    onChange={(e) =>
                      setRagSettings((prev) => ({
                        ...prev,
                        temperature: e.target.value,
                      }))
                    }
                    className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
                  />
                </div>
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground">
                  Số tài liệu tối đa
                </label>
                <input
                  type="number"
                  min="1"
                  max="20"
                  value={ragSettings.max_documents}
                  onChange={(e) =>
                    setRagSettings((prev) => ({
                      ...prev,
                      max_documents: e.target.value,
                    }))
                  }
                  className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
                />
              </div>
              <div className="rounded-xl border border-border/70 bg-background/70 p-3">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="text-xs font-semibold text-foreground">
                      Hybrid Embedding
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Kết hợp keyword + vector để chọn tài liệu RAG.
                    </div>
                  </div>
                  <label className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
                    <input
                      type="checkbox"
                      checked={Boolean(ragSettings.embedding_enabled)}
                      onChange={(e) =>
                        setRagSettings((prev) => ({
                          ...prev,
                          embedding_enabled: e.target.checked,
                        }))
                      }
                      className="h-4 w-4 rounded border-border text-primary focus:ring-primary"
                    />
                    Bật embedding
                  </label>
                </div>
                <div className="mt-3">
                  <label className="text-xs font-medium text-muted-foreground">
                    Tỉ lệ hybrid (0 = keyword, 1 = vector)
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={Number(ragSettings.hybrid_alpha ?? 0.6)}
                    onChange={(e) =>
                      setRagSettings((prev) => ({
                        ...prev,
                        hybrid_alpha: Number(e.target.value),
                      }))
                    }
                    className="mt-2 w-full"
                  />
                  <div className="text-xs text-muted-foreground">
                    {Number(ragSettings.hybrid_alpha ?? 0.6).toFixed(2)}
                  </div>
                </div>
              </div>
              <button
                type="button"
                onClick={handleSaveRagSettings}
                className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
              >
                Lưu cấu hình
              </button>
              <button
                type="button"
                onClick={handleRebuildEmbeddings}
                className="rounded-lg border border-border px-4 py-2 text-sm font-semibold text-foreground hover:bg-muted"
              >
                Tạo lại embedding cho tài liệu
              </button>
            </div>
          </div>

          <div className="rounded-2xl border border-border bg-card p-6 shadow-sm space-y-6">
            <div>
              <h2 className="text-lg font-display font-semibold text-foreground">
                Tài liệu RAG
              </h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Tải file hoặc nhập nội dung thủ công để AI dùng làm nguồn.
              </p>
            </div>

            <div className="space-y-3 rounded-xl border border-border bg-background/40 p-4">
              <h3 className="text-sm font-semibold text-foreground">
                Upload file
              </h3>
              <input
                type="text"
                value={ragTitle}
                onChange={(e) => setRagTitle(e.target.value)}
                placeholder="Tiêu đề (tuỳ chọn)"
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
              />
              <input
                type="file"
                accept=".txt,.md,.json"
                onChange={(e) => setRagFile(e.target.files?.[0] || null)}
                className="w-full text-sm text-muted-foreground"
              />
              <button
                type="button"
                onClick={handleUploadRagFile}
                className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
              >
                Tải file
              </button>
            </div>

            <div className="space-y-3 rounded-xl border border-border bg-background/40 p-4">
              <h3 className="text-sm font-semibold text-foreground">
                Thêm thủ công
              </h3>
              <input
                type="text"
                value={ragTitle}
                onChange={(e) => setRagTitle(e.target.value)}
                placeholder="Tiêu đề"
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
              />
              <textarea
                rows={4}
                value={ragContent}
                onChange={(e) => setRagContent(e.target.value)}
                placeholder="Nội dung..."
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
              />
              <button
                type="button"
                onClick={handleCreateRagDocument}
                className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
              >
                Thêm tài liệu
              </button>
            </div>

            <div className="rounded-xl border border-border bg-background/40 p-4">
              <h3 className="text-sm font-semibold text-foreground">
                Danh sách tài liệu
              </h3>
              {ragLoading ? (
                <div className="mt-3 space-y-2">
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-4 w-2/3" />
                </div>
              ) : (
                <div className="mt-3 space-y-2 max-h-56 overflow-auto">
                  {ragDocuments.map((doc) => (
                    <button
                      key={doc.id}
                      type="button"
                      onClick={() => setSelectedRagDocId(doc.id)}
                      className={[
                        "w-full rounded-lg border px-3 py-2 text-left text-sm",
                        selectedRagDocId === doc.id
                          ? "border-primary bg-primary/10"
                          : "border-border hover:bg-muted",
                      ].join(" ")}
                    >
                      <div className="font-semibold text-foreground">
                        {doc.title}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {doc.source_type} ·{" "}
                        {doc.is_active ? "Đang dùng" : "Tạm tắt"} ·{" "}
                        {doc.has_embedding ? "Embedding ✅" : "Embedding ⏳"}
                      </div>
                    </button>
                  ))}
                  {!ragDocuments.length ? (
                    <div className="text-sm text-muted-foreground">
                      Chưa có tài liệu.
                    </div>
                  ) : null}
                </div>
              )}
            </div>

            {selectedRagDoc ? (
              <div className="space-y-3 rounded-xl border border-border bg-background/40 p-4">
                <h3 className="text-sm font-semibold text-foreground">
                  Chỉnh sửa tài liệu
                </h3>
                <input
                  type="text"
                  value={ragEditForm.title}
                  onChange={(e) =>
                    setRagEditForm((prev) => ({
                      ...prev,
                      title: e.target.value,
                    }))
                  }
                  className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
                />
                <textarea
                  rows={5}
                  value={ragEditForm.content}
                  onChange={(e) =>
                    setRagEditForm((prev) => ({
                      ...prev,
                      content: e.target.value,
                    }))
                  }
                  className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
                />
                <label className="flex items-center gap-2 text-sm text-foreground">
                  <input
                    type="checkbox"
                    checked={ragEditForm.is_active}
                    onChange={(e) =>
                      setRagEditForm((prev) => ({
                        ...prev,
                        is_active: e.target.checked,
                      }))
                    }
                    className="h-4 w-4 rounded border-border text-primary focus:ring-primary"
                  />
                  Kích hoạt tài liệu
                </label>
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={handleUpdateRagDocument}
                    className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
                  >
                    Lưu
                  </button>
                  <button
                    type="button"
                    onClick={() => handleDeleteRagDocument(selectedRagDocId)}
                    className="rounded-lg border border-destructive/40 px-4 py-2 text-sm font-semibold text-destructive hover:bg-destructive/10"
                  >
                    Xoá
                  </button>
                </div>
              </div>
            ) : null}
          </div>

          <div className="rounded-2xl border border-border bg-card p-6 shadow-sm space-y-5 lg:col-span-2">
            <div>
              <h2 className="text-lg font-display font-semibold text-foreground">
                AI tạo nội dung
              </h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Sinh bài học hoặc quiz dựa trên motif, dùng seed hoặc model AI.
              </p>
            </div>

            {aiGenError ? (
              <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
                {aiGenError}
              </div>
            ) : null}
            {aiGenNotice ? (
              <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3 text-sm text-emerald-700">
                {aiGenNotice}
              </div>
            ) : null}

            <div className="grid gap-3 sm:grid-cols-3">
              <input
                type="text"
                value={aiGenMotifId}
                onChange={(e) => setAiGenMotifId(e.target.value)}
                placeholder="Motif ID"
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
              />
              <input
                type="text"
                value={aiGenMotifName}
                onChange={(e) => setAiGenMotifName(e.target.value)}
                placeholder="Tên họa tiết"
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
              />
              <input
                type="text"
                value={aiGenUrnSlug}
                onChange={(e) => setAiGenUrnSlug(e.target.value)}
                placeholder="Urn slug (tuỳ chọn)"
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
              />
            </div>

            <div className="grid gap-3 sm:grid-cols-3">
              <select
                value={aiGenLevel}
                onChange={(e) => setAiGenLevel(e.target.value)}
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
              >
                {AI_LEVEL_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <input
                type="number"
                min="1"
                max="30"
                value={aiGenQuizCount}
                onChange={(e) => setAiGenQuizCount(e.target.value)}
                placeholder="Số câu quiz"
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
              />
              <input
                type="number"
                min="1"
                max="5"
                value={aiGenQuizDifficulty}
                onChange={(e) => setAiGenQuizDifficulty(e.target.value)}
                placeholder="Độ khó (1-5)"
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
              />
            </div>

            <div className="flex flex-wrap gap-4 text-sm text-foreground">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={aiGenUseSeed}
                  onChange={(e) => setAiGenUseSeed(e.target.checked)}
                  className="h-4 w-4 rounded border-border text-primary focus:ring-primary"
                />
                Ưu tiên seed
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={aiGenForceLesson}
                  onChange={(e) => setAiGenForceLesson(e.target.checked)}
                  className="h-4 w-4 rounded border-border text-primary focus:ring-primary"
                />
                Ghi đè bài học
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={aiGenIncludeQuiz}
                  onChange={(e) => setAiGenIncludeQuiz(e.target.checked)}
                  className="h-4 w-4 rounded border-border text-primary focus:ring-primary"
                />
                Tạo quiz kèm bài học
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={aiGenReplaceQuiz}
                  onChange={(e) => setAiGenReplaceQuiz(e.target.checked)}
                  className="h-4 w-4 rounded border-border text-primary focus:ring-primary"
                />
                Xoá quiz cũ
              </label>
            </div>

            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                onClick={handleGenerateLesson}
                disabled={aiGenLoading}
                className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
              >
                Sinh bài học
              </button>
              <button
                type="button"
                onClick={handleGenerateQuiz}
                disabled={aiGenLoading}
                className="rounded-lg border border-border px-4 py-2 text-sm font-semibold text-foreground hover:bg-muted disabled:opacity-60"
              >
                Sinh quiz
              </button>
            </div>
          </div>
        </section>
      )}
    </main>
  );
}
