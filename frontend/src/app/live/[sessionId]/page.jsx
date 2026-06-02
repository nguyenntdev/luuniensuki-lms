"use client";

import { useParams } from "next/navigation";

import LiveClassroom from "@/components/live2/LiveClassroom";

export default function LiveSessionPage() {
  const params = useParams();
  const sessionId = String(params?.sessionId || "");
  return <LiveClassroom sessionId={sessionId} />;
}
