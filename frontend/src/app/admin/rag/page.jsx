import { redirect } from "next/navigation";

export default function AdminRagRedirect() {
  redirect("/admin?tab=rag");
}
