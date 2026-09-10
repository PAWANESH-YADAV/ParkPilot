import { Providers } from "./providers";
import "./globals.css";

export const metadata = {
  title: "ParkPilot - Smart Parking System",
  description: "Autonomous parking lot system using AI, Computer Vision, and IoT",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
