import { useState } from 'react'
import { Github, Plus } from 'lucide-react'

function Settings() {
  const [activeTab, setActiveTab] = useState('profile')
  const [profileData, setProfileData] = useState({
    name: 'John Doe',
    email: 'john@example.com',
    role: 'Project Manager',
  })

  const tabs = [
    { id: 'profile', label: 'Profile' },
    { id: 'team', label: 'Team' },
    { id: 'integrations', label: 'Integrations' },
    { id: 'general', label: 'General' },
    { id: 'security', label: 'Security' },
  ]

  const integrations = [
    {
      id: 1,
      name: 'GitHub',
      description: 'Connect your GitHub repository',
      icon: 'github',
      status: 'Connected',
      connected: true,
    },
    {
      id: 2,
      name: 'Jira',
      description: 'Sync with your Jira project',
      icon: 'jira',
      status: 'Not Connected',
      connected: false,
    },
    {
      id: 3,
      name: 'Slack',
      description: 'Get notifications in Slack',
      icon: 'slack',
      status: 'Connected',
      connected: true,
    },
    {
      id: 4,
      name: 'OpenAI',
      description: 'Connect your OpenAI API key',
      icon: 'openai',
      status: 'Connected',
      connected: true,
    },
  ]

  const teamMembers = [
    { id: 1, name: 'John Doe', role: 'Project Manager', email: 'john@example.com' },
    { id: 2, name: 'Sarah Wilson', role: 'Developer', email: 'sarah@example.com' },
    { id: 3, name: 'Mike Johnson', role: 'Developer', email: 'mike@example.com' },
  ]

  const handleProfileUpdate = (e) => {
    e.preventDefault()
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-text-primary">Settings</h1>
      </div>

      <div className="card">
        <div className="border-b border-border-light flex overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-6 py-4 font-medium text-sm transition-colors whitespace-nowrap ${
                activeTab === tab.id
                  ? 'text-primary border-b-2 border-primary'
                  : 'text-text-secondary hover:text-text-primary'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="p-6">
          {activeTab === 'profile' && (
            <div className="max-w-2xl">
              <h2 className="text-lg font-bold text-text-primary mb-6">Profile Settings</h2>
              <form onSubmit={handleProfileUpdate} className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-text-primary mb-2">Full Name</label>
                  <input
                    type="text"
                    value={profileData.name}
                    onChange={(e) => setProfileData({ ...profileData, name: e.target.value })}
                    className="input-field w-full"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-text-primary mb-2">Email</label>
                  <input
                    type="email"
                    value={profileData.email}
                    onChange={(e) => setProfileData({ ...profileData, email: e.target.value })}
                    className="input-field w-full"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-text-primary mb-2">Role</label>
                  <select
                    value={profileData.role}
                    onChange={(e) => setProfileData({ ...profileData, role: e.target.value })}
                    className="input-field w-full"
                  >
                    <option>Project Manager</option>
                    <option>Developer</option>
                    <option>QA Engineer</option>
                    <option>Product Owner</option>
                  </select>
                </div>

                <button type="submit" className="btn-primary">
                  Save Changes
                </button>
              </form>
            </div>
          )}

          {activeTab === 'team' && (
            <div className="max-w-2xl">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-bold text-text-primary">Team Members</h2>
                <button className="btn-primary flex items-center gap-2">
                  <Plus className="w-5 h-5" />
                  Add Member
                </button>
              </div>

              <div className="space-y-4">
                {teamMembers.map((member) => (
                  <div key={member.id} className="flex items-center justify-between p-4 border border-border-light rounded-lg">
                    <div>
                      <p className="font-medium text-text-primary">{member.name}</p>
                      <p className="text-sm text-text-secondary">{member.email}</p>
                    </div>
                    <div className="text-right">
                      <span className="inline-block bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-xs font-medium">
                        {member.role}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'integrations' && (
            <div>
              <h2 className="text-lg font-bold text-text-primary mb-6">Integrations</h2>
              <p className="text-text-secondary text-sm mb-6">Connect your favorite tools and services</p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {integrations.map((integration) => (
                  <div key={integration.id} className="border border-border-light rounded-lg p-6 flex flex-col justify-between">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h3 className="font-bold text-text-primary mb-1">{integration.name}</h3>
                        <p className="text-sm text-text-secondary">{integration.description}</p>
                      </div>
                      {integration.name === 'GitHub' && (
                        <Github className="w-8 h-8 text-text-secondary" />
                      )}
                    </div>

                    <div className="flex items-center justify-between pt-4 border-t border-border-light">
                      {integration.connected ? (
                        <span className="text-sm font-medium text-green-600">Connected</span>
                      ) : (
                        <span className="text-sm font-medium text-text-secondary">Not Connected</span>
                      )}
                      <button className="text-primary hover:text-primary-dark text-sm font-medium">
                        {integration.connected ? 'Configure' : 'Connect'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'general' && (
            <div className="max-w-2xl">
              <h2 className="text-lg font-bold text-text-primary mb-6">General Settings</h2>
              <div className="space-y-6">
                <div className="flex items-center justify-between p-4 border border-border-light rounded-lg">
                  <div>
                    <p className="font-medium text-text-primary">Email Notifications</p>
                    <p className="text-sm text-text-secondary">Receive email updates about your projects</p>
                  </div>
                  <input type="checkbox" defaultChecked className="w-4 h-4" />
                </div>

                <div className="flex items-center justify-between p-4 border border-border-light rounded-lg">
                  <div>
                    <p className="font-medium text-text-primary">Daily Digest</p>
                    <p className="text-sm text-text-secondary">Get a summary of your daily activities</p>
                  </div>
                  <input type="checkbox" defaultChecked className="w-4 h-4" />
                </div>

                <div className="flex items-center justify-between p-4 border border-border-light rounded-lg">
                  <div>
                    <p className="font-medium text-text-primary">Dark Mode</p>
                    <p className="text-sm text-text-secondary">Use dark theme for the interface</p>
                  </div>
                  <input type="checkbox" className="w-4 h-4" />
                </div>
              </div>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="max-w-2xl">
              <h2 className="text-lg font-bold text-text-primary mb-6">Security Settings</h2>
              <form className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-text-primary mb-2">Current Password</label>
                  <input
                    type="password"
                    className="input-field w-full"
                    placeholder="Enter current password"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-text-primary mb-2">New Password</label>
                  <input
                    type="password"
                    className="input-field w-full"
                    placeholder="Enter new password"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-text-primary mb-2">Confirm Password</label>
                  <input
                    type="password"
                    className="input-field w-full"
                    placeholder="Confirm new password"
                  />
                </div>

                <button type="submit" className="btn-primary">
                  Update Password
                </button>
              </form>

              <div className="mt-8 p-4 bg-red-50 border border-red-200 rounded-lg">
                <h3 className="font-bold text-red-800 mb-2">Danger Zone</h3>
                <p className="text-sm text-red-700 mb-4">Delete your account and all associated data</p>
                <button className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors text-sm font-medium">
                  Delete Account
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Settings
