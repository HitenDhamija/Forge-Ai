'use client';

import React, { useState, useEffect } from 'react';
import { Rocket, GitBranch, Database, GitMerge, Eye, Users, Check, ArrowRight, ArrowLeft, X } from 'lucide-react';
import { useExperienceStore } from '@/stores/experience-store';
import { useRouter } from 'next/navigation';

interface WelcomeWizardProps {
  isOpen: boolean;
  onClose: () => void;
}

const steps = [
  {
    id: 'welcome',
    title: 'Welcome to ForgeAI',
    description: 'Your AI-powered engineering platform. Let\'s get you started!',
    icon: Rocket,
    color: 'from-blue-600 to-purple-600',
  },
  {
    id: 'connect_repo',
    title: 'Connect a Repository',
    description: 'Add your first repository to start analyzing code with AI.',
    icon: GitBranch,
    color: 'from-green-600 to-teal-600',
    route: '/repositories',
  },
  {
    id: 'explore_memory',
    title: 'Explore Memory',
    description: 'See how ForgeAI remembers and learns from your codebase.',
    icon: Database,
    color: 'from-purple-600 to-pink-600',
    route: '/memory',
  },
  {
    id: 'run_workflow',
    title: 'Run a Workflow',
    description: 'Execute your first AI workflow to see the magic in action.',
    icon: GitMerge,
    color: 'from-orange-600 to-red-600',
    route: '/workflows',
  },
  {
    id: 'inspect_results',
    title: 'Inspect Results',
    description: 'Review AI analysis output and explore insights.',
    icon: Eye,
    color: 'from-cyan-600 to-blue-600',
    route: '/review',
  },
  {
    id: 'invite_team',
    title: 'Invite Your Team',
    description: 'Collaborate with team members on your projects.',
    icon: Users,
    color: 'from-pink-600 to-rose-600',
    route: '/organizations',
  },
];

export function WelcomeWizard({ isOpen, onClose }: WelcomeWizardProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const router = useRouter();
  const { onboardingState, fetchOnboardingState, completeOnboardingStep, skipOnboarding } = useExperienceStore();

  useEffect(() => {
    if (isOpen) {
      fetchOnboardingState();
    }
  }, [isOpen, fetchOnboardingState]);

  // Sync with backend state
  useEffect(() => {
    if (onboardingState?.is_complete) {
      setCurrentStep(steps.length);
    }
  }, [onboardingState]);

  if (!isOpen) return null;

  const step = steps[currentStep];
  const isFirstStep = currentStep === 0;
  const isLastStep = currentStep === steps.length - 1;
  const isComplete = currentStep === steps.length;

  const handleNext = async () => {
    if (step?.id) {
      await completeOnboardingStep(step.id);
    }
    if (isLastStep) {
      setCurrentStep(steps.length);
    } else {
      setCurrentStep(prev => prev + 1);
    }
  };

  const handleBack = () => {
    if (!isFirstStep) {
      setCurrentStep(prev => prev - 1);
    }
  };

  const handleSkip = async () => {
    await skipOnboarding();
    onClose();
  };

  const handleNavigateToStep = () => {
    if (step?.route) {
      router.push(step.route);
      onClose();
    }
  };

  if (isComplete) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center">
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm" />
        <div className="relative w-full max-w-lg bg-gray-900 rounded-2xl shadow-2xl border border-gray-800 overflow-hidden">
          <div className="p-8 text-center">
            <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center">
              <Check className="w-10 h-10 text-white" />
            </div>
            <h2 className="text-2xl font-bold text-white mb-4">You&apos;re All Set!</h2>
            <p className="text-gray-400 mb-8">
              ForgeAI is ready to supercharge your engineering workflow.
              Start by exploring the dashboard or running your first analysis.
            </p>
            <button
              onClick={onClose}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
            >
              Get Started
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/70 backdrop-blur-sm" onClick={handleSkip} />
      <div className="relative w-full max-w-2xl bg-gray-900 rounded-2xl shadow-2xl border border-gray-800 overflow-hidden">
        {/* Progress Bar */}
        <div className="h-1 bg-gray-800">
          <div
            className="h-full bg-gradient-to-r from-blue-600 to-purple-600 transition-all duration-300"
            style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
          />
        </div>

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
          <div className="flex items-center gap-2">
            {steps.map((_, i) => (
              <div
                key={i}
                className={`w-2 h-2 rounded-full ${
                  i < currentStep ? 'bg-green-500' : i === currentStep ? 'bg-blue-500' : 'bg-gray-700'
                }`}
              />
            ))}
          </div>
          <button onClick={handleSkip} className="text-gray-400 hover:text-white text-sm">
            Skip
          </button>
        </div>

        {/* Content */}
        <div className="p-8">
          <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${step.color} flex items-center justify-center mb-6`}>
            <step.icon className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-white mb-3">{step.title}</h2>
          <p className="text-gray-400 text-lg">{step.description}</p>

          {step.route && (
            <button
              onClick={handleNavigateToStep}
              className="mt-4 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-sm transition-colors"
            >
              Go to {step.title} →
            </button>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-gray-800">
          <button
            onClick={handleBack}
            disabled={isFirstStep}
            className="flex items-center gap-2 px-4 py-2 text-gray-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </button>
          <button
            onClick={handleNext}
            className="flex items-center gap-2 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
          >
            {isLastStep ? 'Finish' : 'Next'}
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
