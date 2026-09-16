import React, { useState, useRef, useEffect } from 'react';
import {
  Sparkles,
  Send,
  ShieldCheck,
  AlertTriangle,
  Database,
  ArrowRight,
  RotateCcw,
} from 'lucide-react';
import { processAssistantQuery, type AssistantAnswer } from '../../api/assistantEngine';
import { HonestFooter } from '../national/HonestFooter';

interface Message {
  id: string;
  sender: 'user' | 'assistant';
  timestamp: string;
  text?: string;
  answer?: AssistantAnswer;
}

const STARTER_PROMPTS = [
  'What is the risk score of project 705505?',
  'Which Railway projects are deteriorating?',
  'What is the risk profile of Roads & Highways?',
  'National portfolio overview and benchmark',
  'Will project 705505 definitely fail?',
  'Show high-conviction triple-trigger warnings',
];

export const AssistantScreen: React.FC = () => {
  const [queryInput, setQueryInput] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome-msg',
      sender: 'assistant',
      timestamp: 'Ready',
      answer: {
        headline: 'PAIMANA Analyst Assistant (Deterministic Query Router)',
        summary:
          'Welcome to the operational risk query console. Every response is deterministically mapped to verified precomputed endpoints without generative LLM hallucination.',
        entityType: 'methodology',
        matchedQuery: 'init',
        metrics: [
          { label: 'Hallucination Rate', value: '0.0%', highlight: 'low' },
          { label: 'Architecture', value: 'Deterministic Router' },
          { label: 'Data Source', value: 'Precomputed Parquets' },
        ],
        bullets: [
          'Direct lookup by project ID (e.g., 705505, 400119, 400171).',
          'Sector & ministry risk distribution and portfolio aggregates.',
          'Early-warning triage watchlist filtered by trigger strength.',
          'Honest probabilistic risk interpretation (not binary certainties).',
        ],
        sources: [
          {
            endpoint: '/national/summary',
            method: 'GET',
            description: 'Portfolio baseline & lineage registry',
          },
        ],
      },
    },
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (queryText?: string) => {
    const text = (queryText || queryInput).trim();
    if (!text || loading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      sender: 'user',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      text,
    };

    setMessages((prev) => [...prev, userMessage]);
    setQueryInput('');
    setLoading(true);

    try {
      const answer = await processAssistantQuery(text);
      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        sender: 'assistant',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        answer,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      const errorMessage: Message = {
        id: `assistant-err-${Date.now()}`,
        sender: 'assistant',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        answer: {
          headline: 'Query Execution Error',
          summary: `An error occurred while connecting to the verified data backend: ${err?.message || 'Network error'}.`,
          entityType: 'unknown',
          matchedQuery: text,
          sources: [],
        },
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setMessages([
      {
        id: `welcome-${Date.now()}`,
        sender: 'assistant',
        timestamp: 'Ready',
        answer: {
          headline: 'PAIMANA Analyst Assistant (Deterministic Query Router)',
          summary:
            'Welcome to the operational risk query console. Every response is deterministically mapped to verified precomputed endpoints without generative LLM hallucination.',
          entityType: 'methodology',
          matchedQuery: 'init',
          metrics: [
            { label: 'Hallucination Rate', value: '0.0%', highlight: 'low' },
            { label: 'Architecture', value: 'Deterministic Router' },
            { label: 'Data Source', value: 'Precomputed Parquets' },
          ],
          bullets: [
            'Direct lookup by project ID (e.g., 705505, 400119, 400171).',
            'Sector & ministry risk distribution and portfolio aggregates.',
            'Early-warning triage watchlist filtered by trigger strength.',
            'Honest probabilistic risk interpretation (not binary certainties).',
          ],
          sources: [
            {
              endpoint: '/national/summary',
              method: 'GET',
              description: 'Portfolio baseline & lineage registry',
            },
          ],
        },
      },
    ]);
  };

  return (
    <div className="space-y-6">
      {/* Header Banner with Mandatory Deterministic Badge */}
      <div className="bg-bg-surface p-5 rounded-lg border border-border-hairline shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex flex-wrap items-center gap-2.5">
            <h1 className="text-[22px] font-bold text-text-primary tracking-tight">
              Operational Risk Analyst Assistant
            </h1>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded bg-emerald-50 border border-emerald-200 text-emerald-800 text-[11px] font-bold tracking-wide">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              Deterministic Query Router over Validated Data — Zero Hallucination by Construction
            </span>
          </div>
          <p className="text-[13px] text-text-secondary">
            Natural language interface dispatches directly to precomputed FastAPI endpoints without generative fabrication.
          </p>
        </div>

        <button
          type="button"
          onClick={handleReset}
          className="self-start md:self-auto flex items-center gap-1.5 px-3 py-1.5 text-[12px] font-semibold text-text-secondary hover:text-text-primary bg-bg-subtle hover:bg-slate-100 border border-border-hairline rounded transition-colors"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          Reset Chat
        </button>
      </div>

      {/* Quick Prompt Starter Chips */}
      <div className="bg-bg-surface p-4 rounded-lg border border-border-hairline shadow-xs">
        <div className="flex items-center gap-2 mb-2 text-text-muted text-[11px] font-bold uppercase tracking-wider">
          <Sparkles className="w-3.5 h-3.5 text-brand-primary" />
          <span>Recommended Triage Queries:</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {STARTER_PROMPTS.map((prompt, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleSend(prompt)}
              disabled={loading}
              className="text-left px-3 py-1.5 rounded-full bg-slate-50 hover:bg-blue-50 border border-slate-200 hover:border-blue-200 text-[12px] text-text-secondary hover:text-brand-primary font-medium transition-colors flex items-center gap-1.5 group disabled:opacity-50"
            >
              <span>{prompt}</span>
              <ArrowRight className="w-3 h-3 text-slate-400 group-hover:text-brand-primary transition-colors" />
            </button>
          ))}
        </div>
      </div>

      {/* Conversation Area */}
      <div className="bg-bg-surface rounded-lg border border-border-hairline shadow-xs flex flex-col min-h-[520px] max-h-[700px]">
        {/* Messages Stream */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {messages.map((msg) => {
            if (msg.sender === 'user') {
              return (
                <div key={msg.id} className="flex justify-end">
                  <div className="max-w-2xl bg-brand-primary text-white rounded-lg rounded-tr-none px-4 py-3 shadow-xs">
                    <p className="text-[13px] leading-relaxed font-medium">{msg.text}</p>
                    <span className="block text-[10px] text-blue-200 text-right mt-1 font-mono">
                      {msg.timestamp}
                    </span>
                  </div>
                </div>
              );
            }

            const ans = msg.answer!;
            return (
              <div key={msg.id} className="flex justify-start">
                <div className="max-w-3xl w-full bg-slate-50/70 border border-border-hairline rounded-lg rounded-tl-none p-4.5 space-y-3.5 shadow-xs">
                  {/* Headline & Badge */}
                  <div className="flex items-start justify-between gap-3 border-b border-border-hairline/60 pb-2.5">
                    <div className="flex items-center gap-2">
                      <div className="w-6 h-6 rounded bg-brand-primary/10 flex items-center justify-center shrink-0">
                        <Sparkles className="w-3.5 h-3.5 text-brand-primary" />
                      </div>
                      <h3 className="text-[14px] font-bold text-text-primary">{ans.headline}</h3>
                    </div>
                    <span className="text-[10px] text-text-muted font-mono shrink-0">{msg.timestamp}</span>
                  </div>

                  {/* Transfer Caveat (Simpson's Paradox Warning) */}
                  {ans.transferCaveat && (
                    <div className="bg-amber-50 border border-amber-300 rounded p-3 flex items-start gap-2.5 text-[12px] text-amber-900">
                      <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                      <div className="space-y-0.5">
                        <span className="font-bold block text-[11px] uppercase tracking-wider text-amber-900">
                          Transfer Regime Notice
                        </span>
                        <p className="leading-snug text-amber-800">{ans.transferCaveat}</p>
                      </div>
                    </div>
                  )}

                  {/* Summary Text */}
                  <p className="text-[13px] text-text-secondary leading-relaxed font-normal">
                    {ans.summary}
                  </p>

                  {/* Structured Metric Chips */}
                  {ans.metrics && ans.metrics.length > 0 && (
                    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2.5 pt-1">
                      {ans.metrics.map((m, idx) => {
                        let bg = 'bg-white border-slate-200 text-text-primary';
                        if (m.highlight === 'critical') bg = 'bg-risk-critical-bg/40 border-risk-critical/30 text-risk-critical';
                        if (m.highlight === 'high') bg = 'bg-risk-high-bg/40 border-risk-high/30 text-risk-high';
                        if (m.highlight === 'medium') bg = 'bg-risk-medium-bg/40 border-risk-medium/30 text-risk-medium';
                        if (m.highlight === 'low') bg = 'bg-risk-low-bg/40 border-risk-low/30 text-risk-low';

                        return (
                          <div
                            key={idx}
                            className={`p-2.5 rounded border flex flex-col justify-between ${bg}`}
                          >
                            <span className="text-[10px] uppercase font-semibold text-text-muted truncate">
                              {m.label}
                            </span>
                            <span className="text-[14px] font-bold tabular-nums mt-1 truncate">
                              {m.value}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  )}

                  {/* Key Bullets */}
                  {ans.bullets && ans.bullets.length > 0 && (
                    <div className="bg-white p-3 rounded border border-border-hairline space-y-1.5">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-text-muted block">
                        Verified Evidence Points:
                      </span>
                      <ul className="space-y-1 text-[12px] text-text-secondary list-disc pl-4">
                        {ans.bullets.map((b, idx) => (
                          <li key={idx} className="leading-relaxed">
                            {b}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Mandatory Source Attribution Chips */}
                  <div className="pt-2 border-t border-border-hairline/60 flex flex-wrap items-center gap-2">
                    <span className="text-[11px] font-bold text-text-muted flex items-center gap-1">
                      <Database className="w-3 h-3 text-slate-400" />
                      Source Receipt:
                    </span>
                    {ans.sources.map((src, idx) => (
                      <div
                        key={idx}
                        className="inline-flex items-center gap-1.5 px-2 py-1 rounded bg-slate-100 border border-slate-200 text-slate-800 text-[11px] font-mono"
                        title={src.description}
                      >
                        <span className="bg-brand-primary text-white text-[9px] font-bold px-1 py-0.2 rounded">
                          {src.method}
                        </span>
                        <span>{src.endpoint}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            );
          })}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-slate-50 border border-border-hairline rounded-lg rounded-tl-none p-4 flex items-center gap-2.5 text-text-secondary text-[13px]">
                <div className="w-2 h-2 rounded-full bg-brand-primary animate-ping" />
                <span>Querying precomputed endpoint and verifying signatures...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Footer */}
        <div className="p-3.5 border-t border-border-hairline bg-white rounded-b-lg">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex items-center gap-2"
          >
            <input
              type="text"
              value={queryInput}
              onChange={(e) => setQueryInput(e.target.value)}
              placeholder="Query project ID (e.g. 705505), sector (Railways, Power), or portfolio benchmark..."
              className="flex-1 px-3.5 py-2.5 bg-bg-surface border border-border-hairline rounded-md text-[13px] text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-1 focus:ring-brand-primary focus:border-brand-primary"
            />
            <button
              type="submit"
              disabled={loading || !queryInput.trim()}
              className="px-4 py-2.5 bg-brand-primary hover:bg-brand-primary-hover text-white text-[13px] font-semibold rounded-md shadow-xs transition-colors flex items-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Query</span>
            </button>
          </form>
          <div className="mt-2 flex items-center justify-between text-[11px] text-text-muted px-1">
            <span>Powered by deterministic rule routing over panel.parquet</span>
            <span>Zero Generative Hallucination Guarantee</span>
          </div>
        </div>
      </div>

      {/* Verified Methodology Footer */}
      <HonestFooter />
    </div>
  );
};
