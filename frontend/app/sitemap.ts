import { MetadataRoute } from "next";

interface QuestionSummary {
  slug: string;
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const baseUrl =
    process.env.NEXT_PUBLIC_APP_URL ||
    "http://production-dsa-alb-209746966.ap-southeast-2.elb.amazonaws.com";
  const backendUrl = process.env.INTERNAL_API_URL || "http://backend:8000";

  let problems: QuestionSummary[] = [
    { slug: "two-sum" },
    { slug: "valid-parentheses" },
    { slug: "reverse-linked-list" },
    { slug: "two-sum-ii-input-array-is-sorted" },
  ];

  try {
    const res = await fetch(`${backendUrl}/api/v1/questions`, {
      next: { revalidate: 3600 },
      signal: AbortSignal.timeout(3000),
    });
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        problems = data;
      }
    }
  } catch {
    // Fall back to known seeded problem list
  }

  const problemEntries: MetadataRoute.Sitemap = problems.map((p) => ({
    url: `${baseUrl}/problems/${p.slug}`,
    lastModified: new Date(),
    changeFrequency: "weekly",
    priority: 0.8,
  }));

  return [
    {
      url: baseUrl,
      lastModified: new Date(),
      changeFrequency: "daily",
      priority: 1.0,
    },
    ...problemEntries,
  ];
}
