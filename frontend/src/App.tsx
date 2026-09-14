import { useEffect, useMemo, useRef, useState } from "react";
import { runPass1, runPass2, type QuestionShift } from "./api";
import { copy } from "./i18n";
import {
  localizedCardName,
  tarotDeck,
  type Locale,
  type TarotCard,
} from "./deck";

type Phase =
  | "draw"
  | "reflect"
  | "loading-pass1"
  | "pass1"
  | "question"
  | "loading-pass2"
  | "pass2";

const Arrow = () => (
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <path d="M5 12h14M13 6l6 6-6 6" />
  </svg>
);

const Spark = () => (
  <svg viewBox="0 0 32 32" aria-hidden="true">
    <path d="M16 1c.7 9.6 5.4 14.3 15 15-9.6.7-14.3 5.4-15 15C15.3 21.4 10.6 16.7 1 16 10.6 15.3 15.3 10.6 16 1Z" />
  </svg>
);

const Mic = ({ active }: { active: boolean }) => (
  <svg viewBox="0 0 24 24" aria-hidden="true" className={active ? "mic-active" : ""}>
    <rect x="9" y="3" width="6" height="11" rx="3" />
    <path d="M5.5 11.5a6.5 6.5 0 0 0 13 0M12 18v3M8.5 21h7" />
  </svg>
);

const GitHub = () => (
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <path d="M12 2a10 10 0 0 0-3.16 19.49c.5.09.68-.22.68-.48v-1.87c-2.78.6-3.37-1.18-3.37-1.18-.45-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.61.07-.61 1 .07 1.53 1.03 1.53 1.03.9 1.53 2.35 1.09 2.92.83.09-.65.35-1.09.64-1.34-2.22-.25-4.55-1.11-4.55-4.94 0-1.09.39-1.98 1.03-2.68-.1-.25-.45-1.27.1-2.64 0 0 .84-.27 2.75 1.02A9.57 9.57 0 0 1 12 6.82a9.6 9.6 0 0 1 2.5.34c1.92-1.3 2.76-1.02 2.76-1.02.55 1.37.2 2.39.1 2.64.64.7 1.03 1.59 1.03 2.68 0 3.84-2.34 4.68-4.57 4.93.36.31.68.92.68 1.86V21c0 .27.18.58.69.48A10 10 0 0 0 12 2Z" />
  </svg>
);

const getInitialLocale = (): Locale => {
  const stored = localStorage.getItem("liminal-locale");
  if (stored === "zh" || stored === "en") return stored;
  return navigator.language.toLowerCase().startsWith("zh") ? "zh" : "en";
};

const phaseIndex = (phase: Phase) => {
  if (phase === "draw") return 0;
  if (phase === "reflect" || phase === "loading-pass1") return 1;
  if (phase === "pass1") return 2;
  return 3;
};

function App() {
  const [locale, setLocale] = useState<Locale>(getInitialLocale);
  const [heroProgress, setHeroProgress] = useState(0);
  const [phase, setPhase] = useState<Phase>("draw");
  const [card, setCard] = useState<TarotCard | null>(null);
  const [orientation, setOrientation] = useState<"upright" | "reversed">("upright");
  const [transcript, setTranscript] = useState("");
  const [question, setQuestion] = useState("");
  const [shift, setShift] = useState<QuestionShift>("unchanged");
  const [shiftNote, setShiftNote] = useState("");
  const [sessionId, setSessionId] = useState("");
  const [pass1Reading, setPass1Reading] = useState("");
  const [pass2Reading, setPass2Reading] = useState("");
  const [takeaway, setTakeaway] = useState("");
  const [error, setError] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [speechUnavailable, setSpeechUnavailable] = useState(false);

  const heroRef = useRef<HTMLElement>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const speechBaseRef = useRef("");
  const t = copy[locale];

  useEffect(() => {
    document.documentElement.lang = locale === "zh" ? "zh-CN" : "en";
    localStorage.setItem("liminal-locale", locale);
  }, [locale]);

  useEffect(() => {
    let frame = 0;
    const update = () => {
      const hero = heroRef.current;
      if (!hero) return;
      const rect = hero.getBoundingClientRect();
      const distance = Math.max(1, rect.height - window.innerHeight);
      setHeroProgress(Math.min(1, Math.max(0, -rect.top / distance)));
    };
    const onScroll = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(update);
    };
    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("scroll", onScroll);
    };
  }, []);

  const steps = useMemo(
    () => [t.stepCard, t.stepReflect, t.stepPass1, t.stepPass2],
    [t],
  );

  const updatePointer = (event: React.PointerEvent<HTMLElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = ((event.clientX - rect.left) / rect.width) * 100;
    const y = ((event.clientY - rect.top) / rect.height) * 100;
    event.currentTarget.style.setProperty("--pointer-x", `${x}%`);
    event.currentTarget.style.setProperty("--pointer-y", `${y}%`);
    event.currentTarget.style.setProperty("--lens-x", `${event.clientX}px`);
    event.currentTarget.style.setProperty("--lens-y", `${event.clientY}px`);
  };

  const selectLocale = (next: Locale) => setLocale(next);

  const drawCard = () => {
    const next = tarotDeck[Math.floor(Math.random() * tarotDeck.length)];
    setCard(next);
    setOrientation(Math.random() > 0.5 ? "upright" : "reversed");
    setPhase("reflect");
    setError("");
  };

  const submitPass1 = async () => {
    if (!card || !transcript.trim()) return;
    setPhase("loading-pass1");
    setError("");
    try {
      const result = await runPass1({
        card: card.id,
        orientation,
        transcript: transcript.trim(),
      });
      setSessionId(result.session_id);
      setPass1Reading(result.reading);
      setPhase("pass1");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
      setPhase("reflect");
    }
  };

  const submitPass2 = async () => {
    if (!sessionId || !question.trim()) return;
    setPhase("loading-pass2");
    setError("");
    try {
      const result = await runPass2({
        session_id: sessionId,
        question: question.trim(),
        question_shift: shift,
        question_shift_note: shiftNote.trim() || undefined,
      });
      setPass2Reading(result.reading);
      setTakeaway(result.takeaway_question);
      setPhase("pass2");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
      setPhase("question");
    }
  };

  const toggleSpeech = () => {
    if (isListening) {
      recognitionRef.current?.stop();
      return;
    }
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) {
      setSpeechUnavailable(true);
      return;
    }
    const recognition = new Recognition();
    recognition.lang = locale === "zh" ? "zh-CN" : "en-US";
    recognition.continuous = true;
    recognition.interimResults = true;
    speechBaseRef.current = transcript.trim();
    recognition.onresult = (event) => {
      let spoken = "";
      for (let index = 0; index < event.results.length; index += 1) {
        spoken += event.results[index][0].transcript;
      }
      setTranscript(`${speechBaseRef.current} ${spoken}`.trim());
    };
    recognition.onerror = () => setIsListening(false);
    recognition.onend = () => setIsListening(false);
    recognitionRef.current = recognition;
    recognition.start();
    setIsListening(true);
    setSpeechUnavailable(false);
  };

  const restart = () => {
    recognitionRef.current?.stop();
    setPhase("draw");
    setCard(null);
    setTranscript("");
    setQuestion("");
    setShift("unchanged");
    setShiftNote("");
    setSessionId("");
    setPass1Reading("");
    setPass2Reading("");
    setTakeaway("");
    setError("");
  };

  const cardName = card ? localizedCardName(card, locale) : "";
  const orientationLabel = orientation === "upright" ? t.upright : t.reversed;

  return (
    <main>
      <header className="site-nav">
        <a className="mini-wordmark" href="#top" aria-label="Liminal home">
          LIMINAL
        </a>
        <nav aria-label="Primary navigation">
          <a href="#experience">{t.navExperience}</a>
          <a href="#contact">{t.navAbout}</a>
          <div className="locale-switch" aria-label="Language">
            <button
              className={locale === "zh" ? "active" : ""}
              onClick={() => selectLocale("zh")}
              type="button"
            >
              中
            </button>
            <span>/</span>
            <button
              className={locale === "en" ? "active" : ""}
              onClick={() => selectLocale("en")}
              type="button"
            >
              EN
            </button>
          </div>
        </nav>
      </header>

      <section
        id="top"
        className="hero"
        ref={heroRef}
        onPointerMove={updatePointer}
        style={{ "--hero-progress": heroProgress } as React.CSSProperties}
      >
        <div className="hero-stage">
          <div className="star-field" />
          <div className="hero-orb" aria-hidden="true">
            <div className="orb-core" />
            <div className="orb-sheen" />
          </div>
          <div className="pointer-lens" aria-hidden="true" />

          <div className="hero-copy">
            <p className="eyebrow">{t.heroEyebrow}</p>
            <h1 aria-label="Liminal">LIMINAL</h1>
            <div className="hero-statement">
              <span>{t.heroLineA}</span>
              <span>{t.heroLineB}</span>
            </div>
            <p className="hero-description">{t.heroDescription}</p>
          </div>

          <a className="scroll-cue" href="#experience">
            <span>{t.scroll}</span>
            <i><Arrow /></i>
          </a>
          <div className="threshold-label">{t.threshold}</div>
          <div className="threshold-wash" />
        </div>
      </section>

      <section id="experience" className="experience-section">
        <div className="experience-intro">
          <p className="eyebrow dark">{t.experienceEyebrow}</p>
          <h2>{t.experienceTitle}</h2>
          <p>{t.experienceDescription}</p>
        </div>

        <div className="reading-shell">
          <div className="reading-progress" aria-label="Reading progress">
            {steps.map((label, index) => (
              <div
                className={`progress-step ${index <= phaseIndex(phase) ? "active" : ""}`}
                key={label}
              >
                <span>{String(index + 1).padStart(2, "0")}</span>
                <p>{label}</p>
              </div>
            ))}
          </div>

          <div className="reading-workspace">
            {phase === "draw" && (
              <div className="draw-panel panel-enter">
                <div className="deck-visual" aria-hidden="true">
                  <div className="deck-card card-one" />
                  <div className="deck-card card-two" />
                  <div className="deck-card card-top">
                    <Spark />
                    <span>LIMINAL</span>
                  </div>
                </div>
                <div className="panel-copy">
                  <p className="section-number">01 · {t.stepCard}</p>
                  <h3>{t.deckReady}</h3>
                  <p>{t.deckHint}</p>
                  <button className="primary-button" onClick={drawCard} type="button">
                    <span>{t.draw}</span>
                    <Arrow />
                  </button>
                </div>
              </div>
            )}

            {(phase === "reflect" || phase === "loading-pass1") && card && (
              <div className="reflection-panel panel-enter">
                <div className="drawn-card-wrap">
                  <div className={`drawn-card ${orientation === "reversed" ? "is-reversed" : ""}`}>
                    <div className="card-fallback"><Spark /></div>
                    <img src={card.imageUrl} alt={cardName} onError={(event) => { event.currentTarget.style.opacity = "0"; }} />
                  </div>
                  <div className="card-caption">
                    <strong>{cardName}</strong>
                    <span>{orientationLabel}</span>
                  </div>
                  <a href={card.imageUrl} target="_blank" rel="noreferrer" className="image-credit">
                    {t.imageCredit}
                  </a>
                </div>

                <div className="reflection-form">
                  <p className="section-number">02 · {t.stepReflect}</p>
                  <h3>{t.lookPrompt}</h3>
                  <p className="form-hint">{t.lookHint}</p>
                  <div className={`text-field ${isListening ? "listening" : ""}`}>
                    <textarea
                      value={transcript}
                      onChange={(event) => setTranscript(event.target.value)}
                      placeholder={t.transcriptPlaceholder}
                      rows={8}
                      disabled={phase === "loading-pass1"}
                    />
                    <div className="field-actions">
                      <span>{transcript.trim().length}</span>
                      <button onClick={toggleSpeech} type="button" disabled={phase === "loading-pass1"}>
                        <Mic active={isListening} />
                        {isListening ? t.recording : t.record}
                      </button>
                    </div>
                  </div>
                  {speechUnavailable && <p className="inline-note">{t.speechUnavailable}</p>}
                  <p className="privacy-note">{t.privacy}</p>
                  {error && <div className="error-note"><strong>{t.errorTitle}</strong><span>{error}</span></div>}
                  <button
                    className="primary-button wide"
                    onClick={submitPass1}
                    disabled={!transcript.trim() || phase === "loading-pass1"}
                    type="button"
                  >
                    <span>{phase === "loading-pass1" ? t.workingPass1 : t.generatePass1}</span>
                    {phase === "loading-pass1" ? <i className="loading-dot" /> : <Arrow />}
                  </button>
                  {phase === "loading-pass1" && <p className="wait-note">{t.waitNote}</p>}
                </div>
              </div>
            )}

            {phase === "pass1" && (
              <article className="result-panel panel-enter">
                <p className="section-number">{t.pass1Eyebrow}</p>
                <h3>{t.pass1Title}</h3>
                <div className="reading-text">{pass1Reading}</div>
                <button className="primary-button" onClick={() => setPhase("question")} type="button">
                  <span>{t.revealQuestion}</span>
                  <Arrow />
                </button>
              </article>
            )}

            {(phase === "question" || phase === "loading-pass2") && (
              <div className="question-panel panel-enter">
                <div className="question-heading">
                  <p className="section-number">04 · {t.stepPass2}</p>
                  <h3>{t.questionTitle}</h3>
                  <p>{t.questionHint}</p>
                </div>
                <textarea
                  className="question-input"
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  placeholder={t.questionPlaceholder}
                  rows={4}
                  disabled={phase === "loading-pass2"}
                />
                <fieldset className="shift-options">
                  <legend>{t.shiftLabel}</legend>
                  {([
                    ["unchanged", t.shiftUnchanged],
                    ["clarified", t.shiftClarified],
                    ["shifted_focus", t.shiftFocus],
                    ["different_question", t.shiftDifferent],
                  ] as const).map(([value, label]) => (
                    <button
                      type="button"
                      className={shift === value ? "selected" : ""}
                      onClick={() => setShift(value)}
                      key={value}
                      disabled={phase === "loading-pass2"}
                    >
                      <i />
                      {label}
                    </button>
                  ))}
                </fieldset>
                {shift !== "unchanged" && (
                  <input
                    className="shift-note"
                    value={shiftNote}
                    onChange={(event) => setShiftNote(event.target.value)}
                    placeholder={t.shiftNotePlaceholder}
                    disabled={phase === "loading-pass2"}
                  />
                )}
                {error && <div className="error-note"><strong>{t.errorTitle}</strong><span>{error}</span></div>}
                <button
                  className="primary-button wide"
                  onClick={submitPass2}
                  disabled={!question.trim() || phase === "loading-pass2"}
                  type="button"
                >
                  <span>{phase === "loading-pass2" ? t.workingPass2 : t.generatePass2}</span>
                  {phase === "loading-pass2" ? <i className="loading-dot" /> : <Arrow />}
                </button>
                {phase === "loading-pass2" && <p className="wait-note">{t.waitNote}</p>}
              </div>
            )}

            {phase === "pass2" && (
              <article className="result-panel final-result panel-enter">
                <p className="section-number">{t.pass2Eyebrow}</p>
                <h3>{t.pass2Title}</h3>
                <div className="reading-text">{pass2Reading}</div>
                <div className="takeaway-card">
                  <Spark />
                  <p>{t.takeaway}</p>
                  <blockquote>{takeaway}</blockquote>
                </div>
                <button className="text-button" onClick={restart} type="button">
                  {t.restart} <Arrow />
                </button>
              </article>
            )}
          </div>
        </div>
      </section>

      <section id="contact" className="contact-section">
        <div className="contact-aura" aria-hidden="true" />
        <div className="contact-copy">
          <p className="eyebrow">{t.contactEyebrow}</p>
          <h2>{t.contactTitle}</h2>
          <p>{t.contactBody}</p>
          <a className="github-link" href="https://github.com/ElenaLiu-snow" target="_blank" rel="noreferrer">
            <GitHub />
            <span>{t.visitGithub}</span>
            <Arrow />
          </a>
        </div>
        <footer>
          <span>© 2026 LIMINAL</span>
          <span>{t.madeBy}</span>
        </footer>
      </section>
    </main>
  );
}

export default App;
