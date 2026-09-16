import { Providers } from "./providers";
import "./globals.css";

export const metadata = {
  title: "ParkPilot - Smart Parking System",
  description: "Autonomous parking lot system using AI, Computer Vision, and IoT",
};

const noFoucScript = `
(function(){try{
  var k='parkpilot-theme';
  var s=localStorage.getItem(k);
  var t=s==='dark'?'dark':'light';
  var r=document.documentElement;
  if(t==='dark'){r.classList.add('dark');}else{r.classList.remove('dark');}
  r.style.colorScheme=t;
}catch(e){}})();
`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: noFoucScript }} />
      </head>
      <body>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
