/**
 * SynthesisText
 *
 * Renders a synthesis paragraph as clean English prose with inline citation
 * links for any cognitive mechanism names detected in the text.
 *
 * - Sanitizes slash-delimited fragments and stray punctuation
 * - Splits on double newlines into separate <p> elements
 * - Detects mechanism display_names (longest-first, case-insensitive)
 *   and wraps them in citation superscripts linking to the source paper
 */

import mechanisms from '../../data/cognitive_mechanisms.json'

interface MechanismMeta {
  displayName: string
  framework: string
  citation: string
  citationUrl: string | undefined
}

// Build lookup sorted longest-first to prevent shorter names shadowing longer ones
const MECHANISM_META: MechanismMeta[] = [...mechanisms]
  .sort((a, b) => b.display_name.length - a.display_name.length)
  .map(m => ({
    displayName: m.display_name,
    framework:   m.framework ?? '',
    citation:    m.citation ?? '',
    citationUrl: (m as { citation_url?: string }).citation_url ?? undefined,
  }))

const MECHANISM_REGEX = new RegExp(
  `(${MECHANISM_META.map(m => m.displayName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`,
  'gi'
)

// Matches inline citations the LLM writes after mechanism names, e.g. "(Kahan, 2010)"
// We strip these because SynthesisText renders its own linked superscript instead.
const INLINE_CITATION_RE = /\s*\([A-Z][^)]{2,40},\s*\d{4}[a-z]?\)/g

function sanitize(raw: string): string {
  return raw
    .replace(/ \/ /g, ' and ')    // slash-delimited lists → "and"
    .replace(/\/(?=\S)/g, ' ')    // residual slashes with no spaces
    .replace(INLINE_CITATION_RE, '') // strip "(Author, Year)" — replaced by linked superscript
    .replace(/,\./g, '.')         // comma-period artifact
    .replace(/\.{2,}/g, '.')      // multiple dots
    .replace(/[^\S\n]{2,}/g, ' ') // double spaces (preserve newlines for paragraph split)
    .trim()
}

function injectCitations(paragraph: string): React.ReactNode[] {
  const parts = paragraph.split(MECHANISM_REGEX)
  return parts.map((part, i) => {
    const meta = MECHANISM_META.find(
      m => m.displayName.toLowerCase() === part.toLowerCase()
    )
    if (!meta) return part

    const sup = (
      <sup key={`cite-${i}`} className="ml-0.5">
        {meta.citationUrl ? (
          <a
            href={meta.citationUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="font-mono text-[10px] text-[#0f0f0f] opacity-50 hover:opacity-100 underline transition-opacity"
            title={meta.citation}
          >
            [{meta.framework}]
          </a>
        ) : (
          <span
            className="font-mono text-[10px] text-[#0f0f0f] opacity-50 cursor-help"
            title={meta.citation}
          >
            [{meta.framework}]
          </span>
        )}
      </sup>
    )

    return (
      <span key={`mech-${i}`}>
        {part}
        {sup}
      </span>
    )
  })
}

interface Props {
  text: string
  className?: string
}

export default function SynthesisText({ text, className = '' }: Props) {
  if (!text) return null

  const sanitized  = sanitize(text)
  const paragraphs = sanitized.split(/\n\n+/).filter(p => p.trim())

  return (
    <>
      {paragraphs.map((para, i) => (
        <p key={i} className={className} style={i > 0 ? { marginTop: '1em' } : undefined}>
          {injectCitations(para)}
        </p>
      ))}
    </>
  )
}
