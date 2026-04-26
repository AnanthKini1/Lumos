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

    const indicator = meta.citationUrl ? (
      <a
        key={`cite-${i}`}
        href={meta.citationUrl}
        target="_blank"
        rel="noopener noreferrer"
        title={meta.citation}
        className="group relative inline-block ml-0.5 align-middle"
        style={{ textDecoration: 'none' }}
      >
        {/* Small superscript dot */}
        <span
          className="inline-flex items-center justify-center rounded-full font-mono font-bold leading-none
                     text-[#fafafa] bg-[#0f0f0f] opacity-30 group-hover:opacity-80
                     transition-opacity duration-200 cursor-pointer select-none"
          style={{ width: '12px', height: '12px', fontSize: '7px', verticalAlign: 'super' }}
        >
          ¹
        </span>
        {/* Tooltip */}
        <span
          className="pointer-events-none absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5
                     whitespace-nowrap font-mono text-[10px] text-[#fafafa] bg-[#0f0f0f]
                     px-2 py-1 opacity-0 group-hover:opacity-100
                     transition-opacity duration-200 z-50"
          style={{ borderRadius: '2px' }}
        >
          {meta.citation}
        </span>
      </a>
    ) : (
      <span
        key={`cite-${i}`}
        title={meta.citation}
        className="group relative inline-block ml-0.5 align-middle cursor-help"
      >
        <span
          className="inline-flex items-center justify-center rounded-full font-mono font-bold leading-none
                     text-[#fafafa] bg-[#0f0f0f] opacity-30 group-hover:opacity-80
                     transition-opacity duration-200 select-none"
          style={{ width: '12px', height: '12px', fontSize: '7px', verticalAlign: 'super' }}
        >
          ¹
        </span>
        <span
          className="pointer-events-none absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5
                     whitespace-nowrap font-mono text-[10px] text-[#fafafa] bg-[#0f0f0f]
                     px-2 py-1 opacity-0 group-hover:opacity-100
                     transition-opacity duration-200 z-50"
          style={{ borderRadius: '2px' }}
        >
          {meta.citation}
        </span>
      </span>
    )

    return (
      <span key={`mech-${i}`}>
        {part}
        {indicator}
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
