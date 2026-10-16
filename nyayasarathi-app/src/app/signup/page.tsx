import { Suspense } from 'react';
import { Metadata } from 'next';
import { AuthLayout, SignupForm } from '@/components/auth';

export const metadata: Metadata = {
  title: 'Sign Up — NyayaSarathi Legal Intelligence',
  description:
    'Create your NyayaSarathi research account. Begin searching, analyzing, and verifying Indian judicial case law.',
};

export default function SignupPage() {
  return (
    <AuthLayout activeTab="signup">
      <Suspense fallback={null}>
        <SignupForm />
      </Suspense>
    </AuthLayout>
  );
}
