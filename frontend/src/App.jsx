import { useState } from 'react'

function App() {
  const [caseType, setCaseType] = useState('civil')
  const [caseDescription, setCaseDescription] = useState('')
  const [analyzing, setAnalyzing] = useState(false)
  const [result, setResult] = useState(null)

  const sampleCases = {
    civil: {
      text: "A contract dispute between two logistics companies where Party A failed to deliver goods within the stipulated period, citing force majeure due to adverse weather conditions. Party B claims damages worth $150,000 for business disruption.",
      analysis: {
        legalPrecedents: [
          "Mahanagar Telephone Nigam Ltd. vs. Tata Communications (2019) - Held that force majeure clauses must be strictly construed.",
          "Satyabrata Ghose vs. Mugneeram Bangur & Co. (1954) - Established principles of frustration of contract under Section 56."
        ],
        probability: "65% chance of success for Party B (Damages Claimant)",
        keyTakeaway: "Adverse weather alone does not constitute force majeure unless specifically covered under the contract clause. Damages are highly likely to be awarded but might be mitigated based on actual loss quantification.",
        confidence: "88%"
      }
    },
    criminal: {
      text: "An appeal challenging the admissibility of electronic evidence (WhatsApp chats) obtained without a proper certificate under Section 65B of the Indian Evidence Act. The trial court had relied heavily on these chats for conviction.",
      analysis: {
        legalPrecedents: [
          "Anvar P.V. vs. P.K. Basheer (2014) - Held that Section 65B certificate is a mandatory condition precedent.",
          "Arjun Panditrao Khotkar vs. Kailash Kushanrao Gorantyal (2020) - Clarified that the certificate can be produced at a later stage but is mandatory."
        ],
        probability: "78% chance of appeal being allowed (re-trial or acquittal depending on other evidence)",
        keyTakeaway: "Since the Section 65B certificate was completely absent, the secondary electronic evidence is legally inadmissible. The appellate court is likely to set aside the conviction if it is solely based on this evidence.",
        confidence: "92%"
      }
    }
  }

  const handleAnalyze = async () => {
    if (!caseDescription.trim()) return
    setAnalyzing(true)
    setResult(null)
    try {
      const response = await fetch("http://localhost:8000/api/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          case_type: caseType,
          description: caseDescription
        })
      })
      if (!response.ok) {
        throw new Error("Failed to fetch analysis")
      }
      const data = await response.json()
      setResult(data)
    } catch (error) {
      console.error(error)
      setResult({
        probability: "Connection Offline",
        legalPrecedents: ["Could not establish connection with NyayaSarathi API."],
        keyTakeaway: "Ensure the FastAPI server is running on http://localhost:8000.",
        confidence: "0%"
      })
    } finally {
      setAnalyzing(false)
    }
  }

  const loadSample = (type) => {
    setCaseType(type)
    setCaseDescription(sampleCases[type].text)
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-indigo-500 selection:text-white">
      {/* Background decoration */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(99,102,241,0.08),transparent_45%)] pointer-events-none" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom_left,rgba(168,85,247,0.06),transparent_40%)] pointer-events-none" />

      {/* Header */}
      <header className="border-b border-slate-800/80 bg-slate-900/40 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-500 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <span className="text-xl font-bold text-white">न्या</span>
            </div>
            <div>
              <span className="text-lg font-bold tracking-tight bg-gradient-to-r from-white via-indigo-200 to-violet-200 bg-clip-text text-transparent">NyayaSarathi</span>
              <span className="block text-[10px] text-indigo-400 font-semibold tracking-widest uppercase">Decision Support</span>
            </div>
          </div>
          <nav className="flex items-center space-x-6 text-sm font-medium text-slate-300">
            <a href="#dashboard" className="hover:text-indigo-400 transition-colors">Analyzer</a>
            <a href="#stats" className="hover:text-indigo-400 transition-colors">Intelligence</a>
            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              v1.0.0-Beta
            </span>
          </nav>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 relative z-10">
        {/* Hero Section */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight mb-6 bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent leading-tight">
            AI-Powered Judicial Case Intelligence
          </h1>
          <p className="text-lg text-slate-400 mb-8 leading-relaxed">
            Harness advanced machine learning to analyze legal briefs, predict case outcomes, retrieve binding precedents, and accelerate decision-making workflows.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <button
              onClick={() => loadSample('civil')}
              className="px-5 py-3 rounded-xl bg-slate-900 border border-slate-800 hover:border-indigo-500/50 text-slate-300 transition-all font-medium flex items-center gap-2 cursor-pointer group"
            >
              <span className="w-2 h-2 rounded-full bg-emerald-500 group-hover:scale-125 transition-transform" />
              Try Civil Contract Sample
            </button>
            <button
              onClick={() => loadSample('criminal')}
              className="px-5 py-3 rounded-xl bg-slate-900 border border-slate-800 hover:border-violet-500/50 text-slate-300 transition-all font-medium flex items-center gap-2 cursor-pointer group"
            >
              <span className="w-2 h-2 rounded-full bg-violet-500 group-hover:scale-125 transition-transform" />
              Try Criminal Evidence Appeal
            </button>
          </div>
        </div>

        {/* Dashboard Grid */}
        <div id="dashboard" className="grid grid-cols-1 lg:grid-cols-12 gap-8 mb-16 items-start">
          {/* Input Panel */}
          <div className="lg:col-span-7 bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-xl shadow-2xl">
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <span className="text-indigo-400 font-semibold text-lg">01.</span> Input Brief Details
            </h2>

            <div className="mb-4">
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Case Type</label>
              <div className="flex gap-2">
                <button
                  onClick={() => setCaseType('civil')}
                  className={`flex-1 py-2 px-4 rounded-lg border text-sm font-semibold transition-all cursor-pointer ${
                    caseType === 'civil'
                      ? 'bg-indigo-600/20 border-indigo-500 text-indigo-300 shadow-sm shadow-indigo-500/10'
                      : 'bg-slate-900/50 border-slate-800 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Civil Law
                </button>
                <button
                  onClick={() => setCaseType('criminal')}
                  className={`flex-1 py-2 px-4 rounded-lg border text-sm font-semibold transition-all cursor-pointer ${
                    caseType === 'criminal'
                      ? 'bg-violet-600/20 border-violet-500 text-violet-300 shadow-sm shadow-violet-500/10'
                      : 'bg-slate-900/50 border-slate-800 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Criminal Procedure
                </button>
              </div>
            </div>

            <div className="mb-6">
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Case Narrative & Key facts</label>
              <textarea
                value={caseDescription}
                onChange={(e) => setCaseDescription(e.target.value)}
                placeholder="Paste the factual narrative, legal arguments, or case summary here to analyze..."
                rows="6"
                className="w-full bg-slate-950/80 border border-slate-800 rounded-xl p-4 text-slate-200 text-sm focus:outline-none focus:border-indigo-500 transition-colors placeholder:text-slate-600 resize-none font-mono"
              />
            </div>

            <button
              onClick={handleAnalyze}
              disabled={analyzing || !caseDescription.trim()}
              className={`w-full py-4 rounded-xl font-semibold flex items-center justify-center gap-3 transition-all cursor-pointer ${
                analyzing || !caseDescription.trim()
                  ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700/50'
                  : 'bg-gradient-to-r from-indigo-500 to-violet-600 text-white shadow-lg shadow-indigo-500/20 hover:shadow-indigo-500/35 hover:scale-[1.01]'
              }`}
            >
              {analyzing ? (
                <>
                  <svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  <span>Synthesizing Legal Intelligence...</span>
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                  </svg>
                  <span>Analyze Case & Precedents</span>
                </>
              )}
            </button>
          </div>

          {/* Results / Intelligence Panel */}
          <div className="lg:col-span-5 bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-xl shadow-2xl min-h-[460px] flex flex-col">
            <h2 className="text-xl font-bold text-white mb-4 flex items-center justify-between">
              <span className="flex items-center gap-2">
                <span className="text-violet-400 font-semibold text-lg">02.</span> AI Analysis Result
              </span>
              {result && (
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                  Confidence: {result.confidence}
                </span>
              )}
            </h2>

            {!result && !analyzing && (
              <div className="flex-1 flex flex-col items-center justify-center text-center p-8 border border-dashed border-slate-800 rounded-xl bg-slate-950/20">
                <svg className="w-12 h-12 text-slate-700 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <h3 className="text-slate-400 font-semibold mb-1">Awaiting Case Analysis</h3>
                <p className="text-xs text-slate-500 max-w-[240px]">
                  Provide a case narrative or load a sample on the left to review predictive AI decision support.
                </p>
              </div>
            )}

            {analyzing && (
              <div className="flex-1 flex flex-col items-center justify-center text-center p-8 space-y-4">
                <div className="relative w-16 h-16 flex items-center justify-center">
                  <div className="absolute inset-0 rounded-full border-4 border-indigo-500/10 animate-ping" />
                  <div className="w-12 h-12 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />
                </div>
                <div>
                  <h3 className="text-slate-300 font-semibold mb-1">Analyzing Legal Structure</h3>
                  <p className="text-xs text-slate-500 animate-pulse">
                    Scanning database for matching precedents & statutory sections...
                  </p>
                </div>
              </div>
            )}

            {result && !analyzing && (
              <div className="flex-grow space-y-6 animate-fadeIn">
                <div className="p-4 rounded-xl bg-indigo-500/5 border border-indigo-500/10">
                  <h4 className="text-xs font-semibold text-indigo-400 uppercase tracking-wider mb-1">Estimated Outcome</h4>
                  <p className="text-sm font-semibold text-slate-100">{result.probability}</p>
                </div>

                <div>
                  <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Key Precedents Found</h4>
                  <ul className="space-y-3">
                    {result.legalPrecedents.map((precedent, idx) => (
                      <li key={idx} className="text-xs text-slate-300 pl-3 border-l-2 border-indigo-500">
                        {precedent}
                      </li>
                    ))}
                  </ul>
                </div>

                <div>
                  <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Decision Strategy recommendation</h4>
                  <p className="text-xs text-slate-400 leading-relaxed bg-slate-950/40 p-3 rounded-lg border border-slate-800">
                    {result.keyTakeaway}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Stats / Details */}
        <section id="stats" className="border-t border-slate-900 pt-16">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            <div className="bg-slate-900/30 border border-slate-900 rounded-xl p-6 text-center">
              <div className="text-3xl font-extrabold text-white mb-1">88-95%</div>
              <div className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">Prediction Confidence Range</div>
            </div>
            <div className="bg-slate-900/30 border border-slate-900 rounded-xl p-6 text-center">
              <div className="text-3xl font-extrabold text-white mb-1">&lt; 2.5s</div>
              <div className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">Precedent Query Latency</div>
            </div>
            <div className="bg-slate-900/30 border border-slate-900 rounded-xl p-6 text-center">
              <div className="text-3xl font-extrabold text-white mb-1">500k+</div>
              <div className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">Judgments & Statutes Indexed</div>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-900 mt-24 py-8 text-center text-xs text-slate-600">
        <p>© 2026 NyayaSarathi. Developed under Advanced Legal AI Tech Stack.</p>
      </footer>
    </div>
  )
}

export default App
