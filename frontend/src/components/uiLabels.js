export const DOCUMENTS = ["cnic", "utility_bill", "transaction_statement"];
export const DOC_LABELS = { cnic: "CNIC", utility_bill: "Utility bill", transaction_statement: "Transaction statement" };
export const STATUS_LABELS = { draft: "Draft", processing: "Processing", ready_for_review: "Ready for review", needs_manual_review: "Needs manual review", processing_failed: "Processing failed", needs_documents: "Needs documents", approved: "Approved", rejected: "Rejected", request_document: "Request a document" };
export const STATUS_HELP = {
  draft: "Complete your documents and submit when ready.",
  processing: "Your documents are being processed. Updates appear here automatically.",
  ready_for_review: "Your application is waiting for your bank officer’s review.",
  needs_manual_review: "Your bank officer needs to review the documents manually.",
  processing_failed: "Processing could not finish. Your bank officer can retry it.",
  needs_documents: "Your officer has requested a replacement document.",
  approved: "Your bank officer has approved this application.",
  rejected: "Your bank officer has rejected this application. Read the officer’s note.",
};
