// Shared with SessionSummary, which needs the same wording for the mistake
// types it tallies across a whole block rather than one item.
export const TAG_LABELS: Record<string, string> = {
  harmony_backness: 'backness harmony',
  harmony_rounding: 'rounding harmony',
  stem_alternation: 'stem alternation',
  vowel_deletion: 'vowel deletion',
  buffer_missing: 'buffer consonant',
  form_not_processed: 'the ending was skipped',
  rejected_a_good_form: 'rejected a well formed word',
  missed_the_error: 'accepted a broken form',
  unclassified: 'form',
}
