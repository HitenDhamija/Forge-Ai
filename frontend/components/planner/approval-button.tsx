"use client";

import * as React from "react";
import { Check, X, MessageSquare, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Modal,
  ModalContent,
  ModalHeader,
  ModalTitle,
  ModalDescription,
  ModalFooter,
} from "@/components/ui/modal";
import { Badge } from "@/components/ui/badge";

interface ApprovalButtonProps {
  approvalRequired: boolean;
  onApprove: () => void;
  onRequestChanges: (feedback: string) => void;
  isApproving: boolean;
}

export function ApprovalButton({
  approvalRequired,
  onApprove,
  onRequestChanges,
  isApproving,
}: ApprovalButtonProps) {
  const [showConfirmModal, setShowConfirmModal] = React.useState(false);
  const [showChangesModal, setShowChangesModal] = React.useState(false);
  const [feedback, setFeedback] = React.useState("");

  const handleApprove = () => {
    onApprove();
    setShowConfirmModal(false);
  };

  const handleRequestChanges = () => {
    if (!feedback.trim()) return;
    onRequestChanges(feedback.trim());
    setFeedback("");
    setShowChangesModal(false);
  };

  if (!approvalRequired) {
    return (
      <div className="flex items-center space-x-3 rounded-lg border border-success/30 bg-success/5 p-4">
        <ShieldCheck className="h-5 w-5 text-success" />
        <div>
          <p className="text-sm font-medium text-success">
            Auto-approved plan
          </p>
          <p className="text-xs text-text-muted">
            This plan does not require manual approval
          </p>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="flex items-center justify-between rounded-lg border border-border bg-surface p-4">
        <div className="flex items-center space-x-3">
          <div className="rounded-full bg-warning/10 p-2">
            <ShieldCheck className="h-5 w-5 text-warning" />
          </div>
          <div>
            <p className="text-sm font-medium text-text">
              Approval Required
            </p>
            <p className="text-xs text-text-muted">
              Review the plan before execution
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            onClick={() => setShowChangesModal(true)}
            leftIcon={<MessageSquare className="h-4 w-4" />}
          >
            Request Changes
          </Button>
          <Button
            onClick={() => setShowConfirmModal(true)}
            isLoading={isApproving}
            leftIcon={<Check className="h-4 w-4" />}
          >
            Approve Plan
          </Button>
        </div>
      </div>

      <Modal open={showConfirmModal} onOpenChange={setShowConfirmModal}>
        <ModalContent>
          <ModalHeader>
            <ModalTitle>Confirm Plan Approval</ModalTitle>
            <ModalDescription>
              You are about to approve this execution plan. This action will
              authorize the plan to be executed.
            </ModalDescription>
          </ModalHeader>
          <div className="py-4">
            <div className="rounded-lg border border-warning/30 bg-warning/5 p-4">
              <div className="flex items-center space-x-2">
                <ShieldCheck className="h-4 w-4 text-warning" />
                <span className="text-sm font-medium text-warning">
                  Please confirm
                </span>
              </div>
              <p className="mt-2 text-sm text-text-muted">
                Are you sure you want to approve this plan? Tasks will be
                created and assigned based on the execution plan.
              </p>
            </div>
          </div>
          <ModalFooter>
            <Button
              variant="outline"
              onClick={() => setShowConfirmModal(false)}
              leftIcon={<X className="h-4 w-4" />}
            >
              Cancel
            </Button>
            <Button
              onClick={handleApprove}
              isLoading={isApproving}
              leftIcon={<Check className="h-4 w-4" />}
            >
              Confirm Approval
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      <Modal open={showChangesModal} onOpenChange={setShowChangesModal}>
        <ModalContent>
          <ModalHeader>
            <ModalTitle>Request Changes</ModalTitle>
            <ModalDescription>
              Describe what changes you would like to see in this plan.
            </ModalDescription>
          </ModalHeader>
          <div className="py-4">
            <Textarea
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder="Describe the changes you'd like to see..."
              className="min-h-[120px] resize-none"
            />
          </div>
          <ModalFooter>
            <Button
              variant="outline"
              onClick={() => {
                setShowChangesModal(false);
                setFeedback("");
              }}
              leftIcon={<X className="h-4 w-4" />}
            >
              Cancel
            </Button>
            <Button
              onClick={handleRequestChanges}
              disabled={!feedback.trim()}
              leftIcon={<MessageSquare className="h-4 w-4" />}
            >
              Submit Feedback
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  );
}
