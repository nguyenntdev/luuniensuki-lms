/**
 * Example: Integrating Hearts System with Quiz Component
 * 
 * This file demonstrates how to integrate the hearts system
 * with a quiz component to track wrong answers.
 */

"use client";

import { useState } from "react";
import { HeartsDisplay, HeartsRefillModal } from "@/components/hearts";
import useHeartsStore from "@/stores/heartsStore";

interface QuizQuestion {
  id: string;
  text: string;
  options: string[];
  correctAnswer: number;
}

export default function QuizWithHeartsExample() {
  const [showRefillModal, setShowRefillModal] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  
  const hearts = useHeartsStore((state) => state.hearts);
  const consumeHeart = useHeartsStore((state) => state.useHeart);
  const isUnlimited = useHeartsStore((state) => state.isUnlimited);

  const questions: QuizQuestion[] = [
    {
      id: "q1",
      text: "What dynasty is the Cuu Dinh Ky from?",
      options: ["Ly Dynasty", "Tran Dynasty", "Le Dynasty"],
      correctAnswer: 0,
    },
    // Add more questions...
  ];

  const handleAnswer = async (selectedIndex: number) => {
    const question = questions[currentQuestion];
    const isCorrect = selectedIndex === question.correctAnswer;

    if (!isCorrect) {
      // Wrong answer - use a heart
      if (!isUnlimited() && hearts <= 0) {
        // No hearts left - show refill modal
        setShowRefillModal(true);
        return;
      }

      try {
        await consumeHeart("quiz_wrong", {
          quiz_id: "example_quiz",
          question_id: question.id,
          selected_answer: selectedIndex,
          correct_answer: question.correctAnswer,
        });

        // Show feedback that heart was lost
        console.log("Wrong answer! Lost a heart.");
      } catch (error) {
        console.error("Failed to deduct heart:", error);
        // Handle error (e.g., show error message)
      }
    }

    // Continue to next question or show results
    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    } else {
      console.log("Quiz complete!");
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      {/* Hearts Display in Header */}
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-2xl font-bold">Quiz</h1>
        <HeartsDisplay 
          onClick={() => setShowRefillModal(true)}
          showLabel={true}
          showTimer={true}
        />
      </div>

      {/* Question */}
      <div className="bg-card border border-border rounded-xl p-6 mb-4">
        <p className="text-sm text-muted-foreground mb-2">
          Question {currentQuestion + 1} of {questions.length}
        </p>
        <h2 className="text-xl font-semibold mb-4">
          {questions[currentQuestion].text}
        </h2>
        
        <div className="space-y-3">
          {questions[currentQuestion].options.map((option, index) => (
            <button
              key={index}
              onClick={() => handleAnswer(index)}
              className="w-full p-4 text-left border border-border rounded-lg hover:bg-muted/40 transition-colors"
            >
              {option}
            </button>
          ))}
        </div>
      </div>

      {/* Hearts Refill Modal */}
      <HeartsRefillModal
        isOpen={showRefillModal}
        onClose={() => setShowRefillModal(false)}
        onSuccess={(result) => {
          console.log("Hearts refilled:", result);
          setShowRefillModal(false);
        }}
      />
    </div>
  );
}
