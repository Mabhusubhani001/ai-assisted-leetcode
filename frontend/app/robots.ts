import { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  const baseUrl =
    process.env.NEXT_PUBLIC_APP_URL ||
    "http://production-dsa-alb-209746966.ap-southeast-2.elb.amazonaws.com";

  return {
    rules: [
      {
        userAgent: "*",
        allow: ["/", "/problems/*"],
        disallow: ["/api/*", "/_next/*", "/sign-in/*", "/sign-up/*"],
      },
    ],
    sitemap: `${baseUrl}/sitemap.xml`,
  };
}
