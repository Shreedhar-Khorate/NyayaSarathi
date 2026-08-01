import Hero from '@/components/sections/Hero';
import HeroFloatingCards from '@/components/sections/HeroFloatingCards';
import VerificationThread from '@/components/sections/VerificationThread';
import CapabilitiesBento from '@/components/sections/CapabilitiesBento';
import StatsCounters from '@/components/sections/StatsCounters';
import WorkspaceMockup from '@/components/sections/WorkspaceMockup';
import { Navbar, Footer } from '@/components/layout/NavAndFooter';

export default function Home() {
  return (
    <main className="relative min-h-screen bg-obsidian">
      <div className="grain-overlay" />
      <Navbar />
      <Hero />
      <HeroFloatingCards />
      <VerificationThread />
      <StatsCounters />
      <CapabilitiesBento />
      <WorkspaceMockup />
      <Footer />
    </main>
  );
}
