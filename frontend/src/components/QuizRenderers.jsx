"use client";

import { useState, useEffect, useRef } from "react";
import { Check, X, HelpCircle, Image as ImageIcon, MapPin } from "lucide-react";

/**
 * QuizRenderers - Advanced quiz question renderers
 *
 * Includes:
 * - ImageSelectRenderer: For questions with image options
 * - MeshLocationRenderer: For questions about 3D mesh locations
 * - MultipleChoiceRenderer: Standard text-based multiple choice
 */

// =============================================================================
// Multiple Choice Renderer (Standard)
// =============================================================================

export function MultipleChoiceRenderer({
    question,
    options = [],
    selectedOptionId,
    onSelect,
    showResult = false,
    correctOptionId = null,
    disabled = false,
    className = "",
}) {
    const getOptionStyle = (optionId) => {
        const isSelected = selectedOptionId === optionId;
        const isCorrect = correctOptionId === optionId;
        const isWrong = showResult && isSelected && !isCorrect;

        if (showResult) {
            if (isCorrect) {
                return "border-success bg-success/10 text-success";
            }
            if (isWrong) {
                return "border-destructive bg-destructive/10 text-destructive";
            }
            return "border-border bg-muted/50 text-muted-foreground";
        }

        if (isSelected) {
            return "border-primary bg-primary/10 text-primary";
        }

        return "border-border bg-card hover:border-primary/50 hover:bg-primary/5";
    };

    return (
        <div className={`space-y-3 ${className}`}>
            <p className="text-sm font-medium text-foreground leading-relaxed">
                {question}
            </p>

            <div className="space-y-2">
                {options.map((option) => (
                    <button
                        key={option.id}
                        onClick={() => onSelect(option.id)}
                        disabled={disabled || showResult}
                        className={`w-full flex items-center gap-3 rounded-xl border-2 p-4 text-left transition ${getOptionStyle(option.id)} ${disabled ? "cursor-not-allowed opacity-60" : "cursor-pointer"}`}
                    >
                        {/* Radio Circle */}
                        <div
                            className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 ${
                                selectedOptionId === option.id
                                    ? "border-current bg-current"
                                    : "border-current"
                            }`}
                        >
                            {selectedOptionId === option.id && (
                                <div className="h-2 w-2 rounded-full bg-background" />
                            )}
                        </div>

                        {/* Option Text */}
                        <span className="flex-1 text-sm">{option.text}</span>

                        {/* Result Icon */}
                        {showResult && correctOptionId === option.id && (
                            <Check className="h-5 w-5 text-success" />
                        )}
                        {showResult &&
                            selectedOptionId === option.id &&
                            correctOptionId !== option.id && (
                                <X className="h-5 w-5 text-destructive" />
                            )}
                    </button>
                ))}
            </div>
        </div>
    );
}

// =============================================================================
// Image Select Renderer
// =============================================================================

export function ImageSelectRenderer({
    question,
    options = [],
    selectedOptionId,
    onSelect,
    showResult = false,
    correctOptionId = null,
    disabled = false,
    className = "",
}) {
    const getOptionStyle = (optionId) => {
        const isSelected = selectedOptionId === optionId;
        const isCorrect = correctOptionId === optionId;
        const isWrong = showResult && isSelected && !isCorrect;

        if (showResult) {
            if (isCorrect) {
                return "ring-4 ring-success border-success";
            }
            if (isWrong) {
                return "ring-4 ring-destructive border-destructive";
            }
            return "opacity-50";
        }

        if (isSelected) {
            return "ring-4 ring-primary border-primary";
        }

        return "border-border hover:border-primary/50";
    };

    const getOverlayStyle = (optionId) => {
        const isSelected = selectedOptionId === optionId;
        const isCorrect = correctOptionId === optionId;
        const isWrong = showResult && isSelected && !isCorrect;

        if (showResult && isCorrect) {
            return "bg-success/20";
        }
        if (isWrong) {
            return "bg-destructive/20";
        }
        if (isSelected) {
            return "bg-primary/20";
        }
        return "bg-transparent group-hover:bg-primary/10";
    };

    return (
        <div className={`space-y-4 ${className}`}>
            {/* Question */}
            <div className="flex items-start gap-2">
                <ImageIcon className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                <p className="text-sm font-medium text-foreground leading-relaxed">
                    {question}
                </p>
            </div>

            {/* Image Grid */}
            <div className="grid grid-cols-2 gap-3">
                {options.map((option) => (
                    <button
                        key={option.id}
                        onClick={() => onSelect(option.id)}
                        disabled={disabled || showResult}
                        className={`group relative aspect-square overflow-hidden rounded-xl border-2 transition ${getOptionStyle(option.id)} ${disabled ? "cursor-not-allowed" : "cursor-pointer"}`}
                    >
                        {/* Image */}
                        {option.image_url ? (
                            <img
                                src={option.image_url}
                                alt={option.text || `Option ${option.id}`}
                                className="h-full w-full object-cover"
                                loading="lazy"
                            />
                        ) : (
                            <div className="flex h-full w-full items-center justify-center bg-muted">
                                <ImageIcon className="h-8 w-8 text-muted-foreground" />
                            </div>
                        )}

                        {/* Overlay */}
                        <div
                            className={`absolute inset-0 transition ${getOverlayStyle(option.id)}`}
                        />

                        {/* Selection Indicator */}
                        {selectedOptionId === option.id && !showResult && (
                            <div className="absolute right-2 top-2 flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground">
                                <Check className="h-4 w-4" />
                            </div>
                        )}

                        {/* Result Indicator */}
                        {showResult && correctOptionId === option.id && (
                            <div className="absolute right-2 top-2 flex h-6 w-6 items-center justify-center rounded-full bg-success text-white">
                                <Check className="h-4 w-4" />
                            </div>
                        )}
                        {showResult &&
                            selectedOptionId === option.id &&
                            correctOptionId !== option.id && (
                                <div className="absolute right-2 top-2 flex h-6 w-6 items-center justify-center rounded-full bg-destructive text-white">
                                    <X className="h-4 w-4" />
                                </div>
                            )}

                        {/* Label */}
                        {option.text && (
                            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-2">
                                <span className="text-xs font-medium text-white line-clamp-2">
                                    {option.text}
                                </span>
                            </div>
                        )}
                    </button>
                ))}
            </div>
        </div>
    );
}

// =============================================================================
// Mesh Location Renderer
// =============================================================================

export function MeshLocationRenderer({
    question,
    options = [],
    selectedOptionId,
    onSelect,
    showResult = false,
    correctOptionId = null,
    targetMeshName = null,
    meshAnnotations = null,
    disabled = false,
    onMeshClick = null,
    className = "",
}) {
    const [mode, setMode] = useState("list"); // "list" or "3d"
    const [meshSelected, setMeshSelected] = useState(null);

    // If mesh annotations are available, show 3D mode option
    const has3DSupport = meshAnnotations && targetMeshName;

    const handleMeshSelect = (meshName) => {
        setMeshSelected(meshName);
        // Find option that matches this mesh
        const matchingOption = options.find(
            (opt) => opt.mesh_name === meshName || opt.id === meshName
        );
        if (matchingOption) {
            onSelect(matchingOption.id);
        }
        onMeshClick?.(meshName);
    };

    const getOptionStyle = (optionId) => {
        const isSelected = selectedOptionId === optionId;
        const isCorrect = correctOptionId === optionId;
        const isWrong = showResult && isSelected && !isCorrect;

        if (showResult) {
            if (isCorrect) {
                return "border-success bg-success/10 text-success";
            }
            if (isWrong) {
                return "border-destructive bg-destructive/10 text-destructive";
            }
            return "border-border bg-muted/50 text-muted-foreground";
        }

        if (isSelected) {
            return "border-primary bg-primary/10 text-primary";
        }

        return "border-border bg-card hover:border-primary/50 hover:bg-primary/5";
    };

    return (
        <div className={`space-y-4 ${className}`}>
            {/* Question */}
            <div className="flex items-start gap-2">
                <MapPin className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                <p className="text-sm font-medium text-foreground leading-relaxed">
                    {question}
                </p>
            </div>

            {/* Mode Toggle (if 3D is available) */}
            {has3DSupport && (
                <div className="flex items-center gap-2 rounded-lg bg-muted p-1">
                    <button
                        onClick={() => setMode("list")}
                        className={`flex-1 rounded-md px-3 py-1.5 text-xs font-medium transition ${
                            mode === "list"
                                ? "bg-background text-foreground shadow-sm"
                                : "text-muted-foreground hover:text-foreground"
                        }`}
                    >
                        Danh sách
                    </button>
                    <button
                        onClick={() => setMode("3d")}
                        className={`flex-1 rounded-md px-3 py-1.5 text-xs font-medium transition ${
                            mode === "3d"
                                ? "bg-background text-foreground shadow-sm"
                                : "text-muted-foreground hover:text-foreground"
                        }`}
                    >
                        Chọn trên 3D
                    </button>
                </div>
            )}

            {/* List Mode */}
            {mode === "list" && (
                <div className="space-y-2">
                    {options.map((option) => (
                        <button
                            key={option.id}
                            onClick={() => onSelect(option.id)}
                            disabled={disabled || showResult}
                            className={`w-full flex items-center gap-3 rounded-xl border-2 p-3 text-left transition ${getOptionStyle(option.id)} ${disabled ? "cursor-not-allowed opacity-60" : "cursor-pointer"}`}
                        >
                            {/* Location Icon */}
                            <div
                                className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${
                                    selectedOptionId === option.id
                                        ? "bg-current/20"
                                        : "bg-muted"
                                }`}
                            >
                                <MapPin className="h-4 w-4" />
                            </div>

                            {/* Option Content */}
                            <div className="flex-1 min-w-0">
                                <span className="text-sm font-medium block truncate">
                                    {option.text}
                                </span>
                                {option.description && (
                                    <span className="text-xs text-muted-foreground block truncate">
                                        {option.description}
                                    </span>
                                )}
                            </div>

                            {/* Result Icon */}
                            {showResult && correctOptionId === option.id && (
                                <Check className="h-5 w-5 text-success shrink-0" />
                            )}
                            {showResult &&
                                selectedOptionId === option.id &&
                                correctOptionId !== option.id && (
                                    <X className="h-5 w-5 text-destructive shrink-0" />
                                )}
                        </button>
                    ))}
                </div>
            )}

            {/* 3D Mode Placeholder */}
            {mode === "3d" && (
                <div className="rounded-xl border-2 border-dashed border-border bg-muted/50 p-8 text-center">
                    <MapPin className="mx-auto h-8 w-8 text-muted-foreground" />
                    <p className="mt-2 text-sm text-muted-foreground">
                        Chọn vị trí trên mô hình 3D
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">
                        Click vào vị trí bạn muốn chọn trên mô hình
                    </p>

                    {/* Mesh selection feedback */}
                    {meshSelected && (
                        <div className="mt-4 rounded-lg bg-primary/10 p-3">
                            <span className="text-sm font-medium text-primary">
                                Đã chọn: {meshSelected}
                            </span>
                        </div>
                    )}
                </div>
            )}

            {/* Hint for 3D mode fallback */}
            {!has3DSupport && options.length > 0 && (
                <p className="text-xs text-muted-foreground">
                    💡 Chọn vị trí từ danh sách bên dưới
                </p>
            )}
        </div>
    );
}

// =============================================================================
// True/False Renderer
// =============================================================================

export function TrueFalseRenderer({
    question,
    selectedOptionId,
    onSelect,
    showResult = false,
    correctOptionId = null,
    disabled = false,
    className = "",
}) {
    const options = [
        { id: "true", text: "Đúng", icon: "✓" },
        { id: "false", text: "Sai", icon: "✗" },
    ];

    const getOptionStyle = (optionId) => {
        const isSelected = selectedOptionId === optionId;
        const isCorrect = correctOptionId === optionId;
        const isWrong = showResult && isSelected && !isCorrect;

        if (showResult) {
            if (isCorrect) {
                return "border-success bg-success/10 text-success";
            }
            if (isWrong) {
                return "border-destructive bg-destructive/10 text-destructive";
            }
            return "border-border bg-muted/50 text-muted-foreground";
        }

        if (isSelected) {
            return "border-primary bg-primary/10 text-primary";
        }

        return "border-border bg-card hover:border-primary/50 hover:bg-primary/5";
    };

    return (
        <div className={`space-y-4 ${className}`}>
            <p className="text-sm font-medium text-foreground leading-relaxed">
                {question}
            </p>

            <div className="grid grid-cols-2 gap-3">
                {options.map((option) => (
                    <button
                        key={option.id}
                        onClick={() => onSelect(option.id)}
                        disabled={disabled || showResult}
                        className={`flex flex-col items-center gap-2 rounded-xl border-2 p-4 transition ${getOptionStyle(option.id)} ${disabled ? "cursor-not-allowed opacity-60" : "cursor-pointer"}`}
                    >
                        <span className="text-2xl">{option.icon}</span>
                        <span className="text-sm font-medium">{option.text}</span>

                        {/* Result Icon */}
                        {showResult && correctOptionId === option.id && (
                            <Check className="h-5 w-5 text-success" />
                        )}
                        {showResult &&
                            selectedOptionId === option.id &&
                            correctOptionId !== option.id && (
                                <X className="h-5 w-5 text-destructive" />
                            )}
                    </button>
                ))}
            </div>
        </div>
    );
}

// =============================================================================
// Fill in the Blank Renderer
// =============================================================================

export function FillBlankRenderer({
    question,
    selectedOptionId,
    onSelect,
    showResult = false,
    correctOptionId = null,
    disabled = false,
    className = "",
}) {
    const [inputValue, setInputValue] = useState("");

    const handleInputChange = (e) => {
        const value = e.target.value;
        setInputValue(value);
        onSelect(value.trim().toLowerCase());
    };

    const isCorrect = showResult && selectedOptionId === correctOptionId;
    const isWrong = showResult && selectedOptionId !== correctOptionId;

    // Parse question to find blank position (marked with ___)
    const parts = question.split(/_{3,}/);
    const hasBlank = parts.length > 1;

    return (
        <div className={`space-y-4 ${className}`}>
            {hasBlank ? (
                <div className="text-sm font-medium text-foreground leading-relaxed">
                    {parts[0]}
                    <input
                        type="text"
                        value={inputValue}
                        onChange={handleInputChange}
                        disabled={disabled || showResult}
                        placeholder="..."
                        className={`mx-1 inline-block w-32 rounded-lg border-2 px-3 py-1 text-center transition ${
                            showResult
                                ? isCorrect
                                    ? "border-success bg-success/10"
                                    : "border-destructive bg-destructive/10"
                                : "border-primary bg-primary/5 focus:outline-none focus:ring-2 focus:ring-primary"
                        } ${disabled ? "cursor-not-allowed" : ""}`}
                    />
                    {parts[1]}
                </div>
            ) : (
                <>
                    <p className="text-sm font-medium text-foreground leading-relaxed">
                        {question}
                    </p>
                    <input
                        type="text"
                        value={inputValue}
                        onChange={handleInputChange}
                        disabled={disabled || showResult}
                        placeholder="Nhập câu trả lời..."
                        className={`w-full rounded-xl border-2 px-4 py-3 transition ${
                            showResult
                                ? isCorrect
                                    ? "border-success bg-success/10"
                                    : "border-destructive bg-destructive/10"
                                : "border-border bg-card focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                        } ${disabled ? "cursor-not-allowed" : ""}`}
                    />
                </>
            )}

            {/* Result Feedback */}
            {showResult && (
                <div
                    className={`flex items-center gap-2 rounded-lg p-3 ${
                        isCorrect
                            ? "bg-success/10 text-success"
                            : "bg-destructive/10 text-destructive"
                    }`}
                >
                    {isCorrect ? (
                        <Check className="h-5 w-5" />
                    ) : (
                        <X className="h-5 w-5" />
                    )}
                    <span className="text-sm">
                        {isCorrect
                            ? "Chính xác!"
                            : `Đáp án đúng: ${correctOptionId}`}
                    </span>
                </div>
            )}
        </div>
    );
}

// =============================================================================
// Quiz Question Renderer (Main Component)
// =============================================================================

export default function QuizQuestionRenderer({
    question,
    questionType = "multiple_choice",
    options = [],
    selectedOptionId,
    onSelect,
    showResult = false,
    correctOptionId = null,
    targetMeshName = null,
    meshAnnotations = null,
    disabled = false,
    className = "",
}) {
    // Normalize question type
    const type = questionType?.toLowerCase?.() || "multiple_choice";

    switch (type) {
        case "image_select":
            return (
                <ImageSelectRenderer
                    question={question}
                    options={options}
                    selectedOptionId={selectedOptionId}
                    onSelect={onSelect}
                    showResult={showResult}
                    correctOptionId={correctOptionId}
                    disabled={disabled}
                    className={className}
                />
            );

        case "mesh_location":
            return (
                <MeshLocationRenderer
                    question={question}
                    options={options}
                    selectedOptionId={selectedOptionId}
                    onSelect={onSelect}
                    showResult={showResult}
                    correctOptionId={correctOptionId}
                    targetMeshName={targetMeshName}
                    meshAnnotations={meshAnnotations}
                    disabled={disabled}
                    className={className}
                />
            );

        case "true_false":
            return (
                <TrueFalseRenderer
                    question={question}
                    selectedOptionId={selectedOptionId}
                    onSelect={onSelect}
                    showResult={showResult}
                    correctOptionId={correctOptionId}
                    disabled={disabled}
                    className={className}
                />
            );

        case "fill_blank":
            return (
                <FillBlankRenderer
                    question={question}
                    selectedOptionId={selectedOptionId}
                    onSelect={onSelect}
                    showResult={showResult}
                    correctOptionId={correctOptionId}
                    disabled={disabled}
                    className={className}
                />
            );

        case "multiple_choice":
        default:
            return (
                <MultipleChoiceRenderer
                    question={question}
                    options={options}
                    selectedOptionId={selectedOptionId}
                    onSelect={onSelect}
                    showResult={showResult}
                    correctOptionId={correctOptionId}
                    disabled={disabled}
                    className={className}
                />
            );
    }
}
