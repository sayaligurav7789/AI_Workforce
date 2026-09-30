import { useEffect, useState } from 'react'
import { MessageCircle, Zap, BookOpen, CheckCircle, Play, AlertCircle } from 'lucide-react'
import { agents } from '../data/agents'
import AnalysisResults from '../components/analysis/AnalysisResults'
import apiService from '../services/api'

function AIAgents() {
  const [projects, setProjects] = useState([])
  const [selectedProjectId, setSelectedProjectId] = useState('')
  const [runs, setRuns] = useState([])
  const [analysis, setAnalysis] = useState(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [error, setError] = useState('')

  const loadAgentState = async (projectId) => {
    if (!projectId) return
    try {
      const [runList, result] = await Promise.all([
        apiService.requirements.getRuns(projectId),
        apiService.requirements.getAnalysis(projectId),
      ])
      setRuns(runList)
      setAnalysis(result)
      setError('')
    } catch (requestError) {
      setRuns([])
      setAnalysis(null)
      if (!requestError.message.includes('404')) setError(requestError.message)
    }
  }

  useEffect(() => {
    apiService.projects.getAll()
      .then((items) => {
        setProjects(items)
        if (items.length) setSelectedProjectId(String(items[0].id))
      })
      .catch((requestError) => setError(requestError.message))
  }, [])

  useEffect(() => { loadAgentState(selectedProjectId) }, [selectedProjectId])

  const requirementRun = runs.find((run) => run.agent_name === 'Requirements Analyst AI')
  const requirementStatus = requirementRun?.status || 'READY'

  const handleAnalyze = async () => {
    if (!selectedProjectId) {
      setError('Create a project and upload an SRS before analysis.')
      return
    }
    setIsAnalyzing(true)
    setError('')
    try {
      const result = await apiService.requirements.analyze(selectedProjectId)
      setAnalysis(result)
      await loadAgentState(selectedProjectId)
    } catch (requestError) {
      setError(requestError.message)
      await loadAgentState(selectedProjectId)
    } finally {
      setIsAnalyzing(false)
    }
  }

  const getAgentIcon = (iconName) => ({
    requirement: <BookOpen className="w-8 h-8" />,
    project: <Zap className="w-8 h-8" />,
    developer: <CheckCircle className="w-8 h-8" />,
    qa: <CheckCircle className="w-8 h-8" />,
  }[iconName] || <MessageCircle className="w-8 h-8" />)

  return (
    <div>
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-8">
        <div><h1 className="text-3xl font-bold text-text-primary mb-2">AI Agents Hub</h1><p className="text-text-secondary">Run the Requirements Analyst against your project SRS</p></div>
        <label className="text-sm text-text-secondary">Project
          <select value={selectedProjectId} onChange={(e) => setSelectedProjectId(e.target.value)} className="input-field ml-3">
            {!projects.length && <option value="">No projects</option>}
            {projects.map((project) => <option key={project.id} value={project.id}>{project.name}</option>)}
          </select>
        </label>
      </div>

      {error && <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center gap-2"><AlertCircle className="w-4 h-4" />{error}</div>}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {agents.map((agent) => {
          const isRequirements = agent.icon === 'requirement'
          return (
            <div key={agent.id} className="card p-6 flex flex-col">
              <div className="flex items-center justify-between mb-4">
                <div className="bg-primary-light p-3 rounded-lg text-primary">{getAgentIcon(agent.icon)}</div>
                <div className={`w-3 h-3 rounded-full ${isRequirements && requirementStatus === 'FAILED' ? 'bg-red-500' : isRequirements && requirementStatus === 'PROCESSING' ? 'bg-yellow-500' : 'bg-green-500'}`} />
              </div>
              <h3 className="font-bold text-text-primary mb-2">{agent.name}</h3>
              <p className="text-text-secondary text-sm mb-4 flex-1">{agent.description}</p>
              {isRequirements ? (
                <button onClick={handleAnalyze} disabled={isAnalyzing || !selectedProjectId || requirementStatus === 'PROCESSING'} className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-60">
                  <Play className="w-4 h-4" /> {isAnalyzing || requirementStatus === 'PROCESSING' ? 'Analyzing...' : requirementStatus === 'COMPLETED' ? 'Run Again' : 'Analyze Requirements'}
                </button>
              ) : <button disabled className="btn-secondary w-full opacity-60">Available later</button>}
              <span className="text-xs text-text-secondary mt-2 text-center">Status: {isRequirements ? requirementStatus : 'NOT IMPLEMENTED'}</span>
            </div>
          )
        })}
      </div>

      {analysis?.latest_agent_run?.status === 'COMPLETED' && (
        <div className="card p-6 mb-8">
          <h2 className="text-lg font-bold text-text-primary mb-4">Latest Requirements Analysis</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <Metric label="Functional requirements" value={analysis.functional_requirements.length} />
            <Metric label="User stories" value={analysis.user_stories.length} />
            <Metric label="Acceptance criteria" value={analysis.acceptance_criteria.length} />
            <Metric label="Ambiguities" value={analysis.ambiguities.length} />
          </div>
          <AnalysisResults analysis={analysis} />
        </div>
      )}

      <div className="card p-6">
        <h2 className="text-lg font-bold text-text-primary mb-6">Agent Activity</h2>
        {!runs.length && <p className="text-sm text-text-secondary">No Requirements Analyst runs for this project yet.</p>}
        <div className="space-y-4">
          {runs.map((run) => (
            <div key={run.id} className="flex items-start gap-4 pb-4 border-b border-border-light last:border-b-0">
              <div className="flex-1"><p className="font-medium text-text-primary text-sm">{run.agent_name}</p><p className="text-text-secondary text-sm mt-1">{run.error || `${run.status}${run.output_summary?.requirements_generated ? ` — ${run.output_summary.requirements_generated} requirements generated` : ''}`}</p></div>
              <p className="text-xs text-text-secondary whitespace-nowrap">{run.completed_at ? new Date(run.completed_at).toLocaleString() : 'In progress'}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function Metric({ label, value }) {
  return <div className="bg-bg-light rounded-lg p-4"><p className="text-2xl font-bold text-primary">{value}</p><p className="text-xs text-text-secondary mt-1">{label}</p></div>
}

export default AIAgents