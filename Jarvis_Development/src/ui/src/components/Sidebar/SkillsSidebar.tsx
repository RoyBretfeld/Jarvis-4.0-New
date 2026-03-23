/**
 * AWP-026 – Skills Sidebar
 * Visualisiert alle aktiven Skills vom Librarian-Agent (/api/skills).
 * AWP-030: Zeigt auch AWP-Fortschritt aus useJarvisState.
 */
'use client';

import React, { useEffect, useState } from 'react';
import { useJarvisState } from '@/hooks/useJarvisState';

interface Skill {
  name: string;
  description: string;
  version: string;
  tools: string[];
}

const TOOL_ICON: Record<string, string> = {
  terminal: '⌨',
  docker_api: '🐳',
  security_audit_lib: '🔒',
  rag_access: '🧠',
  ux_validator: '🎨',
};

export function SkillsSidebar() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loadingSkills, setLoadingSkills] = useState(true);
  const { state, aura } = useJarvisState();

  useEffect(() => {
    fetch('/api/skills')
      .then((r) => r.json())
      .then((data: Skill[]) => { setSkills(data); setLoadingSkills(false); })
      .catch(() => setLoadingSkills(false));
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
      {/* System Status */}
      <Section title="System Status">
        <StatusRow label="Phase" value={state?.current_phase ?? '…'} />
        <StatusRow label="Aura" value={aura.toUpperCase()} accent />
        <StatusRow label="OWASP" value={state?.security?.owasp_scan ?? '…'} />
        <StatusRow
          label="Findings"
          value={`${state?.security?.critical_findings ?? 0} critical`}
          danger={(state?.security?.critical_findings ?? 0) > 0}
        />
      </Section>

      {/* AWP Progress */}
      <Section title="AWP Progress">
        {state
          ? <AwpSummary workpackages={state.workpackages} />
          : <Placeholder text="Loading state…" />}
      </Section>

      {/* Active Skills */}
      <Section title={`Skills (${skills.length})`}>
        {loadingSkills
          ? <Placeholder text="Loading skills…" />
          : skills.map((s) => <SkillCard key={s.name} skill={s} />)}
      </Section>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ borderBottom: '1px solid var(--color-border)' }}>
      <div style={{
        padding: '6px var(--spacing-md)',
        fontSize: 10,
        fontWeight: 700,
        letterSpacing: '0.12em',
        textTransform: 'uppercase',
        color: 'var(--color-text-muted)',
        background: 'var(--color-bg-tertiary)',
      }}>
        {title}
      </div>
      <div style={{ padding: '4px 0' }}>{children}</div>
    </div>
  );
}

function StatusRow({
  label, value, accent, danger,
}: { label: string; value: string; accent?: boolean; danger?: boolean }) {
  return (
    <div style={{
      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      padding: '3px var(--spacing-md)',
      fontSize: 12,
    }}>
      <span style={{ color: 'var(--color-text-muted)' }}>{label}</span>
      <span style={{
        color: danger
          ? 'var(--aura-alert-primary)'
          : accent
          ? 'var(--aura-primary)'
          : 'var(--color-text-secondary)',
        fontFamily: 'var(--font-mono)',
        fontSize: 11,
      }}>
        {value}
      </span>
    </div>
  );
}

function ProgressRow({ id, status }: { id: string; status: string }) {
  const color = status === 'COMPLETED'
    ? 'var(--aura-ok-primary)'
    : status === 'IN_PROGRESS'
    ? 'var(--aura-proc-primary)'
    : status === 'SKIPPED'
    ? 'var(--color-text-muted)'
    : 'var(--color-border-focus)';

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6,
      padding: '2px var(--spacing-md)', fontSize: 11 }}>
      <span style={{ color, fontSize: 10, flexShrink: 0 }}>
        {status === 'COMPLETED' ? '✓' : status === 'IN_PROGRESS' ? '◉' : '·'}
      </span>
      <span style={{ color: 'var(--color-text-secondary)', fontFamily: 'var(--font-mono)' }}>
        {id}
      </span>
    </div>
  );
}

function AwpSummary({ workpackages }: { workpackages: Record<string, { status: string }> }) {
  const entries = Object.values(workpackages);
  const total = entries.length;
  const completed = entries.filter((w) => w.status === 'COMPLETED').length;
  const inProgress = entries.filter((w) => w.status === 'IN_PROGRESS').length;
  const pct = total > 0 ? Math.round((completed / total) * 100) : 0;

  return (
    <div style={{ padding: '6px var(--spacing-md)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
        <span style={{ color: 'var(--color-text-muted)' }}>Completed</span>
        <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--aura-ok-primary)' }}>
          {completed}/{total}
        </span>
      </div>
      {inProgress > 0 && (
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginTop: 2 }}>
          <span style={{ color: 'var(--color-text-muted)' }}>In Progress</span>
          <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--aura-proc-primary)' }}>
            {inProgress}
          </span>
        </div>
      )}
      <div style={{
        marginTop: 6, height: 4, borderRadius: 2,
        background: 'var(--color-border)',
        overflow: 'hidden',
      }}>
        <div style={{
          height: '100%', width: `${pct}%`,
          background: 'var(--aura-ok-primary)',
          borderRadius: 2,
          transition: 'width 0.3s ease',
        }} />
      </div>
      <div style={{ fontSize: 10, color: 'var(--color-text-muted)', marginTop: 2, textAlign: 'right' }}>
        {pct}%
      </div>
    </div>
  );
}

function SkillCard({ skill }: { skill: Skill }) {
  return (
    <div style={{
      margin: '2px var(--spacing-sm)',
      padding: '6px var(--spacing-sm)',
      background: 'var(--color-bg-elevated)',
      borderRadius: 4,
      border: '1px solid var(--color-border)',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-primary)' }}>
          {skill.name}
        </span>
        <span style={{ fontSize: 10, color: 'var(--aura-primary)',
          fontFamily: 'var(--font-mono)' }}>
          v{skill.version}
        </span>
      </div>
      <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginTop: 2 }}>
        {skill.description.slice(0, 60)}{skill.description.length > 60 ? '…' : ''}
      </div>
      <div style={{ display: 'flex', gap: 4, marginTop: 4, flexWrap: 'wrap' }}>
        {skill.tools.map((t) => (
          <span key={t} style={{
            fontSize: 10, padding: '1px 4px',
            background: 'var(--color-bg-tertiary)',
            border: '1px solid var(--color-border)',
            borderRadius: 3, color: 'var(--color-text-muted)',
          }}>
            {TOOL_ICON[t] ?? '·'} {t}
          </span>
        ))}
      </div>
    </div>
  );
}

function Placeholder({ text }: { text: string }) {
  return (
    <div style={{ padding: 'var(--spacing-sm) var(--spacing-md)',
      fontSize: 12, color: 'var(--color-text-muted)' }}>
      {text}
    </div>
  );
}
