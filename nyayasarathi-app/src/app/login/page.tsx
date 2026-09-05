import { Metadata } from 'next';
import { AuthLayout, LoginForm } from '@/components/auth';

export const metadata: Metadata = {
  title: 'Login — NyayaSarathi Legal Intelligence',
  description:
    'Sign in to your NyayaSarathi research workspace. Access intelligent judicial case intelligence, hybrid search, and verifiable citations.',
};

export default function LoginPage() {
  return (
    <AuthLayout activeTab="login">
      <LoginForm />
    </AuthLayout>
  );
}
