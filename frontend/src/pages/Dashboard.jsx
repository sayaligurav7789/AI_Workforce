import { Folder, CheckSquare, CheckCircle, AlertCircle } from 'lucide-react'
import StatCard from '../components/common/StatCard'
import ProgressBar from '../components/common/ProgressBar'
import { projects } from '../data/projects'
import { activities } from '../data/activities'

function Dashboard() {
  const userName = localStorage.getItem('userName') || 'John'

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-text-primary mb-2">Good morning, {userName}</h1>
        <p className="text-text-secondary">Here's what's happening with your projects today.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Projects"
          value="12"
          change="+2 this week"
          icon={Folder}
          trend="up"
        />
        <StatCard
          title="Tasks"
          value="48"
          change="+6 this week"
          icon={CheckSquare}
          trend="up"
        />
        <StatCard
          title="Completed"
          value="24"
          change="+10 this week"
          icon={CheckCircle}
          trend="up"
        />
        <StatCard
          title="Overdue"
          value="5"
          change="-2 this week"
          icon={AlertCircle}
          trend="down"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div className="card p-6">
            <h2 className="text-lg font-bold text-text-primary mb-6">Project Progress</h2>
            <div className="space-y-6">
              {projects.slice(0, 4).map((project) => (
                <div key={project.id} className="flex items-center justify-between">
                  <div className="flex-1 mr-4">
                    <div className="flex justify-between mb-2">
                      <p className="font-medium text-text-primary">{project.name}</p>
                      <span className="text-sm text-text-secondary">{project.progress}%</span>
                    </div>
                    <ProgressBar progress={project.progress} showLabel={false} />
                  </div>
                </div>
              ))}
            </div>
            <a href="/projects" className="text-primary hover:text-primary-dark text-sm font-medium mt-6 inline-block">
              View all projects
            </a>
          </div>
        </div>

        <div>
          <div className="card p-6">
            <h2 className="text-lg font-bold text-text-primary mb-6">Recent Activity</h2>
            <div className="space-y-4">
              {activities.slice(0, 4).map((activity) => (
                <div key={activity.id} className="pb-4 border-b border-border-light last:border-b-0">
                  <p className="text-sm text-text-primary font-medium">{activity.description}</p>
                  <p className="text-xs text-text-secondary mt-1">{activity.timestamp}</p>
                </div>
              ))}
            </div>
            <a href="#" className="text-primary hover:text-primary-dark text-sm font-medium mt-4 inline-block">
              View all activity
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
