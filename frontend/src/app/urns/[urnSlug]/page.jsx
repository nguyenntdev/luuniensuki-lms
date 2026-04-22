import UrnExperience from "@/components/UrnExperience";

export default function Page({ params }) {
    return <UrnExperience urnSlug={params.urnSlug} />;
}
