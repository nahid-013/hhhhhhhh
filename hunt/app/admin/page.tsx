'use client'

import { useState, useEffect } from 'react'

type Element = 'AIR' | 'WATER' | 'EARTH' | 'LIGHTNING' | 'FOREST'
type Rarity = 'COMMON' | 'RARE' | 'EPIC' | 'LEGENDARY' | 'MYTHIC'

type SpiritTemplate = {
  id: string
  name: string
  element: Element
  rarity: Rarity
  generation: number
  baseManeuver: number
  baseImpulse: number
  baseFluidity: number
  baseDepth: number
  baseReaction: number
  baseFlow: number
}

type Spirit = {
  id: string
  templateId: string
  template: SpiritTemplate
  ownerId?: string
  owner?: {
    id: string
    telegramId?: string
    walletAddress?: string
  }
  level: number
  xp: number
  hunger: number
  energy: number
  maxEnergy: number
  maneuver: number
  impulse: number
  fluidity: number
  depth: number
  reaction: number
  flow: number
}

type Player = {
  id: string
  telegramId?: string
  walletAddress?: string
  isBanned: boolean
  bannedAt?: string
  banReason?: string
}

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState<'templates' | 'spirits' | 'players'>('templates')
  const [templates, setTemplates] = useState<SpiritTemplate[]>([])
  const [spirits, setSpirits] = useState<Spirit[]>([])
  const [players, setPlayers] = useState<Player[]>([])
  const [showTemplateForm, setShowTemplateForm] = useState(false)
  const [showSpiritForm, setShowSpiritForm] = useState(false)
  const [showPlayerForm, setShowPlayerForm] = useState(false)
  const [editingTemplate, setEditingTemplate] = useState<SpiritTemplate | null>(null)
  const [editingSpirit, setEditingSpirit] = useState<Spirit | null>(null)
  const [editingPlayer, setEditingPlayer] = useState<Player | null>(null)
  const [selectedPlayer, setSelectedPlayer] = useState<string>('')
  const [selectedSpirit, setSelectedSpirit] = useState<string>('')
  const [banningPlayer, setBanningPlayer] = useState<Player | null>(null)
  const [banReason, setBanReason] = useState<string>('')

  useEffect(() => {
    const saved = localStorage.getItem('adminActiveTab')
    if (saved === 'templates' || saved === 'spirits' || saved === 'players') {
      setActiveTab(saved)
    }
    loadTemplates()
    loadSpirits()
    loadPlayers()
  }, [])

  useEffect(() => {
    localStorage.setItem('adminActiveTab', activeTab)
  }, [activeTab])

  const loadTemplates = async () => {
    const res = await fetch('/api/admin/templates')
    const data = await res.json()
    setTemplates(data)
  }

  const loadSpirits = async () => {
    const res = await fetch('/api/admin/spirits')
    const data = await res.json()
    setSpirits(data)
  }

  const loadPlayers = async () => {
    const res = await fetch('/api/admin/players')
    const data = await res.json()
    setPlayers(data)
  }

  const handleCreateTemplate = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const form = e.currentTarget
    const formData = new FormData(form)
    const data = {
      name: formData.get('name'),
      element: formData.get('element'),
      rarity: formData.get('rarity'),
      generation: parseInt(formData.get('generation') as string) || 1,
      baseManeuver: parseInt(formData.get('baseManeuver') as string) || 10,
      baseImpulse: parseInt(formData.get('baseImpulse') as string) || 10,
      baseFluidity: parseInt(formData.get('baseFluidity') as string) || 10,
      baseDepth: parseInt(formData.get('baseDepth') as string) || 10,
      baseReaction: parseInt(formData.get('baseReaction') as string) || 10,
      baseFlow: parseInt(formData.get('baseFlow') as string) || 10,
    }

    await fetch('/api/admin/templates', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })

    form.reset()
    loadTemplates()
    setShowTemplateForm(false)
  }

  const handleUpdateTemplate = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!editingTemplate) return

    const formData = new FormData(e.currentTarget)
    const data = {
      name: formData.get('name'),
      element: formData.get('element'),
      rarity: formData.get('rarity'),
      generation: parseInt(formData.get('generation') as string),
      baseManeuver: parseInt(formData.get('baseManeuver') as string),
      baseImpulse: parseInt(formData.get('baseImpulse') as string),
      baseFluidity: parseInt(formData.get('baseFluidity') as string),
      baseDepth: parseInt(formData.get('baseDepth') as string),
      baseReaction: parseInt(formData.get('baseReaction') as string),
      baseFlow: parseInt(formData.get('baseFlow') as string),
    }

    await fetch(`/api/admin/templates/${editingTemplate.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })

    loadTemplates()
    setEditingTemplate(null)
  }

  const handleDeleteTemplate = async (id: string) => {
    if (!confirm('Удалить шаблон?')) return

    await fetch(`/api/admin/templates/${id}`, {
      method: 'DELETE',
    })

    loadTemplates()
  }

  const handleCreateSpirit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const form = e.currentTarget
    const formData = new FormData(form)
    const data = {
      templateId: formData.get('templateId'),
      ownerId: formData.get('ownerId') || undefined,
      level: parseInt(formData.get('level') as string) || 1,
      xp: parseInt(formData.get('xp') as string) || 0,
      hunger: parseInt(formData.get('hunger') as string) || 100,
      energy: parseInt(formData.get('energy') as string) || 100,
      maxEnergy: parseInt(formData.get('maxEnergy') as string) || 100,
      maneuver: parseInt(formData.get('maneuver') as string) || undefined,
      impulse: parseInt(formData.get('impulse') as string) || undefined,
      fluidity: parseInt(formData.get('fluidity') as string) || undefined,
      depth: parseInt(formData.get('depth') as string) || undefined,
      reaction: parseInt(formData.get('reaction') as string) || undefined,
      flow: parseInt(formData.get('flow') as string) || undefined,
    }

    await fetch('/api/admin/spirits', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })

    form.reset()
    loadSpirits()
    setShowSpiritForm(false)
  }

  const handleUpdateSpirit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!editingSpirit) return

    const formData = new FormData(e.currentTarget)
    const data: any = {}
    if (formData.get('level')) data.level = parseInt(formData.get('level') as string)
    if (formData.get('xp')) data.xp = parseInt(formData.get('xp') as string)
    if (formData.get('hunger')) data.hunger = parseInt(formData.get('hunger') as string)
    if (formData.get('energy')) data.energy = parseInt(formData.get('energy') as string)
    if (formData.get('maxEnergy')) data.maxEnergy = parseInt(formData.get('maxEnergy') as string)
    if (formData.get('maneuver')) data.maneuver = parseInt(formData.get('maneuver') as string)
    if (formData.get('impulse')) data.impulse = parseInt(formData.get('impulse') as string)
    if (formData.get('fluidity')) data.fluidity = parseInt(formData.get('fluidity') as string)
    if (formData.get('depth')) data.depth = parseInt(formData.get('depth') as string)
    if (formData.get('reaction')) data.reaction = parseInt(formData.get('reaction') as string)
    if (formData.get('flow')) data.flow = parseInt(formData.get('flow') as string)
    const ownerId = formData.get('ownerId')
    data.ownerId = ownerId || null

    await fetch(`/api/admin/spirits/${editingSpirit.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })

    loadSpirits()
    setEditingSpirit(null)
  }

  const handleDeleteSpirit = async (id: string) => {
    if (!confirm('Удалить спирит?')) return

    await fetch(`/api/admin/spirits/${id}`, {
      method: 'DELETE',
    })

    loadSpirits()
  }

  const handleAddSpiritToPlayer = async () => {
    if (!selectedPlayer || !selectedSpirit) return

    await fetch(`/api/admin/players/${selectedPlayer}/spirits`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ spiritId: selectedSpirit }),
    })

    loadPlayers()
    loadSpirits()
    setSelectedPlayer('')
    setSelectedSpirit('')
  }

  const handleCreatePlayer = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const form = e.currentTarget
    const formData = new FormData(form)
    const data = {
      telegramId: formData.get('telegramId') || undefined,
      walletAddress: formData.get('walletAddress') || undefined,
    }

    await fetch('/api/admin/players', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })

    form.reset()
    loadPlayers()
    setShowPlayerForm(false)
  }

  const handleUpdatePlayer = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!editingPlayer) return

    const formData = new FormData(e.currentTarget)
    const data: any = {}
    if (formData.get('telegramId')) data.telegramId = formData.get('telegramId')
    if (formData.get('walletAddress')) data.walletAddress = formData.get('walletAddress')

    await fetch(`/api/admin/players/${editingPlayer.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })

    loadPlayers()
    setEditingPlayer(null)
  }

  const handleDeletePlayer = async (id: string) => {
    if (!confirm('Удалить игрока?')) return

    await fetch(`/api/admin/players/${id}`, {
      method: 'DELETE',
    })

    loadPlayers()
  }

  const filteredTemplates = templates
    .filter(t => 
      t.name.toLowerCase().includes(templateNameFilter.toLowerCase()) &&
      t.element.toLowerCase().includes(templateElementFilter.toLowerCase()) &&
      t.rarity.toLowerCase().includes(templateRarityFilter.toLowerCase())
    )
    .sort((a, b) => {
      const aVal = a[templateSort]
      const bVal = b[templateSort]
      const mult = templateSortDir === 'asc' ? 1 : -1
      return aVal > bVal ? mult : aVal < bVal ? -mult : 0
    })

  const filteredSpirits = spirits
    .filter(s => 
      s.template.name.toLowerCase().includes(spiritNameFilter.toLowerCase()) &&
      s.template.element.toLowerCase().includes(spiritElementFilter.toLowerCase())
    )
    .sort((a, b) => {
      let aVal: any, bVal: any
      if (spiritSort === 'name') {
        aVal = a.template.name
        bVal = b.template.name
      } else if (spiritSort === 'level') {
        aVal = a.level
        bVal = b.level
      } else {
        aVal = a.energy
        bVal = b.energy
      }
      const mult = spiritSortDir === 'asc' ? 1 : -1
      return aVal > bVal ? mult : aVal < bVal ? -mult : 0
    })

  const filteredPlayers = players
    .filter(p => 
      (playerTelegramFilter === '' || p.telegramId?.toLowerCase().includes(playerTelegramFilter.toLowerCase())) &&
      (playerWalletFilter === '' || p.walletAddress?.toLowerCase().includes(playerWalletFilter.toLowerCase()))
    )

  const toggleTemplateSort = (key: keyof SpiritTemplate) => {
    if (templateSort === key) {
      setTemplateSortDir(templateSortDir === 'asc' ? 'desc' : 'asc')
    } else {
      setTemplateSort(key)
      setTemplateSortDir('asc')
    }
  }

  const toggleSpiritSort = (key: 'name' | 'level' | 'energy') => {
    if (spiritSort === key) {
      setSpiritSortDir(spiritSortDir === 'asc' ? 'desc' : 'asc')
    } else {
      setSpiritSort(key)
      setSpiritSortDir('asc')
    }
  }

  const handleBanPlayer = async () => {
    if (!banningPlayer) return

    await fetch(`/api/admin/players/${banningPlayer.id}/ban`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason: banReason }),
    })

    loadPlayers()
    setBanningPlayer(null)
    setBanReason('')
  }

  const handleUnbanPlayer = async (playerId: string) => {
    await fetch(`/api/admin/players/${playerId}/ban`, {
      method: 'DELETE',
    })

    loadPlayers()
  }

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-8 text-gray-900">Админка HUNT</h1>

        <div className="flex gap-4 mb-6 border-b">
          <button
            onClick={() => setActiveTab('templates')}
            className={`px-4 py-2 ${activeTab === 'templates' ? 'border-b-2 border-blue-500' : ''}`}
          >
            Шаблоны
          </button>
          <button
            onClick={() => setActiveTab('spirits')}
            className={`px-4 py-2 ${activeTab === 'spirits' ? 'border-b-2 border-blue-500' : ''}`}
          >
            Спириты
          </button>
          <button
            onClick={() => setActiveTab('players')}
            className={`px-4 py-2 ${activeTab === 'players' ? 'border-b-2 border-blue-500' : ''}`}
          >
            Игроки
          </button>
        </div>

        {activeTab === 'templates' && (
          <div>
            <button
              onClick={() => setShowTemplateForm(!showTemplateForm)}
              className="mb-2 px-2 py-1 bg-blue-500 text-white rounded text-xs"
            >
              {showTemplateForm ? 'Отмена' : 'Добавить шаблон'}
            </button>

            {showTemplateForm && (
              <form onSubmit={handleCreateTemplate} className="mb-6 p-4 bg-white rounded shadow">
                <h2 className="text-xl font-bold mb-4">Новый шаблон</h2>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Название</label>
                    <input name="name" required className="w-full p-2 border rounded" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Элемент</label>
                    <select name="element" required className="w-full p-2 border rounded">
                      <option value="AIR">Воздух</option>
                      <option value="WATER">Вода</option>
                      <option value="EARTH">Земля</option>
                      <option value="LIGHTNING">Молния</option>
                      <option value="FOREST">Лес</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Редкость</label>
                    <select name="rarity" required className="w-full p-2 border rounded">
                      <option value="COMMON">Обычный</option>
                      <option value="RARE">Редкий</option>
                      <option value="EPIC">Эпик</option>
                      <option value="LEGENDARY">Легендарный</option>
                      <option value="MYTHIC">Мифик</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Поколение</label>
                    <input name="generation" type="number" defaultValue={1} className="w-full p-2 border rounded" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Маневр</label>
                    <input name="baseManeuver" type="number" defaultValue={10} className="w-full p-2 border rounded" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Импульс</label>
                    <input name="baseImpulse" type="number" defaultValue={10} className="w-full p-2 border rounded" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Текучесть</label>
                    <input name="baseFluidity" type="number" defaultValue={10} className="w-full p-2 border rounded" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Глубинность</label>
                    <input name="baseDepth" type="number" defaultValue={10} className="w-full p-2 border rounded" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Реакция</label>
                    <input name="baseReaction" type="number" defaultValue={10} className="w-full p-2 border rounded" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Поток</label>
                    <input name="baseFlow" type="number" defaultValue={10} className="w-full p-2 border rounded" />
                  </div>
                </div>
                <button type="submit" className="mt-4 px-4 py-2 bg-green-500 text-white rounded">
                  Создать
                </button>
              </form>
            )}

            {editingTemplate && (
              <form onSubmit={handleUpdateTemplate} className="mb-6 p-4 bg-white rounded shadow">
                <h2 className="text-xl font-bold mb-4">Редактировать шаблон</h2>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Название</label>
                    <input name="name" required defaultValue={editingTemplate.name} className="w-full p-2 border rounded" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Элемент</label>
                    <select name="element" required defaultValue={editingTemplate.element} className="w-full p-2 border rounded">
                      <option value="AIR">Воздух</option>
                      <option value="WATER">Вода</option>
                      <option value="EARTH">Земля</option>
                      <option value="LIGHTNING">Молния</option>
                      <option value="FOREST">Лес</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Редкость</label>
                    <select name="rarity" required defaultValue={editingTemplate.rarity} className="w-full p-2 border rounded">
                      <option value="COMMON">Обычный</option>
                      <option value="RARE">Редкий</option>
                      <option value="EPIC">Эпик</option>
                      <option value="LEGENDARY">Легендарный</option>
                      <option value="MYTHIC">Мифик</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Поколение</label>
                    <input name="generation" type="number" defaultValue={editingTemplate.generation} className="w-full p-2 border rounded" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Маневр</label>
                    <input name="baseManeuver" type="number" defaultValue={editingTemplate.baseManeuver} className="w-full p-2 border rounded" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Импульс</label>
                    <input name="baseImpulse" type="number" defaultValue={editingTemplate.baseImpulse} className="w-full p-2 border rounded" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Текучесть</label>
                    <input name="baseFluidity" type="number" defaultValue={editingTemplate.baseFluidity} className="w-full p-2 border rounded" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Глубинность</label>
                    <input name="baseDepth" type="number" defaultValue={editingTemplate.baseDepth} className="w-full p-2 border rounded" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Реакция</label>
                    <input name="baseReaction" type="number" defaultValue={editingTemplate.baseReaction} className="w-full p-2 border rounded" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Поток</label>
                    <input name="baseFlow" type="number" defaultValue={editingTemplate.baseFlow} className="w-full p-2 border rounded" />
                  </div>
                </div>
                <div className="flex gap-2 mt-4">
                  <button type="submit" className="px-4 py-2 bg-green-500 text-white rounded">
                    Сохранить
                  </button>
                  <button
                    type="button"
                    onClick={() => setEditingTemplate(null)}
                    className="px-4 py-2 bg-gray-500 text-white rounded"
                  >
                    Отмена
                  </button>
                </div>
              </form>
            )}

            <button
              onClick={() => setShowTemplateFilters(!showTemplateFilters)}
              className="mb-2 px-2 py-1 bg-gray-500 text-white rounded text-xs"
            >
              {showTemplateFilters ? 'Скрыть фильтры' : 'Показать фильтры'}
            </button>

            {showTemplateFilters && (
              <div className="mb-4 p-3 bg-white rounded shadow">
                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className="block text-xs font-medium mb-1">Название</label>
                    <input
                      type="text"
                      placeholder="Фильтр..."
                      value={templateNameFilter}
                      onChange={(e) => setTemplateNameFilter(e.target.value)}
                      className="w-full p-1 border rounded text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium mb-1">Элемент</label>
                    <select
                      value={templateElementFilter}
                      onChange={(e) => setTemplateElementFilter(e.target.value)}
                      className="w-full p-1 border rounded text-sm"
                    >
                      <option value="">Все</option>
                      <option value="AIR">AIR</option>
                      <option value="WATER">WATER</option>
                      <option value="EARTH">EARTH</option>
                      <option value="LIGHTNING">LIGHTNING</option>
                      <option value="FOREST">FOREST</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium mb-1">Редкость</label>
                    <select
                      value={templateRarityFilter}
                      onChange={(e) => setTemplateRarityFilter(e.target.value)}
                      className="w-full p-1 border rounded text-sm"
                    >
                      <option value="">Все</option>
                      <option value="COMMON">COMMON</option>
                      <option value="RARE">RARE</option>
                      <option value="EPIC">EPIC</option>
                      <option value="LEGENDARY">LEGENDARY</option>
                      <option value="MYTHIC">MYTHIC</option>
                    </select>
                  </div>
                </div>
              </div>
            )}

            <div className="bg-white rounded shadow overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-100 border-b">
                  <tr>
                    <th className="p-3 text-left cursor-pointer hover:bg-gray-200" onClick={() => toggleTemplateSort('name')}>
                      Название {templateSort === 'name' && (templateSortDir === 'asc' ? '↑' : '↓')}
                    </th>
                    <th className="p-3 text-left cursor-pointer hover:bg-gray-200" onClick={() => toggleTemplateSort('element')}>
                      Элемент {templateSort === 'element' && (templateSortDir === 'asc' ? '↑' : '↓')}
                    </th>
                    <th className="p-3 text-left cursor-pointer hover:bg-gray-200" onClick={() => toggleTemplateSort('rarity')}>
                      Редкость {templateSort === 'rarity' && (templateSortDir === 'asc' ? '↑' : '↓')}
                    </th>
                    <th className="p-3 text-left cursor-pointer hover:bg-gray-200" onClick={() => toggleTemplateSort('generation')}>
                      Поколение {templateSort === 'generation' && (templateSortDir === 'asc' ? '↑' : '↓')}
                    </th>
                    <th className="p-3 text-left">Статы</th>
                    <th className="p-3 text-right">Действия</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredTemplates.map((template) => (
                    <tr key={template.id} className="border-b hover:bg-gray-50">
                      <td className="p-3 font-medium">{template.name}</td>
                      <td className="p-3">{template.element}</td>
                      <td className="p-3">{template.rarity}</td>
                      <td className="p-3">{template.generation}</td>
                      <td className="p-3 text-xs">
                        М{template.baseManeuver} И{template.baseImpulse} Т{template.baseFluidity} Г{template.baseDepth} Р{template.baseReaction} П{template.baseFlow}
                      </td>
                      <td className="p-3 text-right">
                        <div className="flex gap-2 justify-end">
                          <button
                            onClick={() => setEditingTemplate(template)}
                            className="px-2 py-1 bg-blue-500 text-white rounded text-xs"
                          >
                            Изм
                          </button>
                          <button
                            onClick={() => handleDeleteTemplate(template.id)}
                            className="px-2 py-1 bg-red-500 text-white rounded text-xs"
                          >
                            Удал
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'spirits' && (
          <div>
            <button
              onClick={() => setShowSpiritForm(!showSpiritForm)}
              className="mb-2 px-2 py-1 bg-blue-500 text-white rounded text-xs"
            >
              {showSpiritForm ? 'Отмена' : 'Добавить спирит'}
            </button>

            {showSpiritForm && (
              <form onSubmit={handleCreateSpirit} className="mb-6 p-4 bg-white rounded shadow">
                <h2 className="text-xl font-bold mb-4">Новый спирит</h2>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Шаблон</label>
                    <select name="templateId" required className="w-full p-2 border rounded">
                      <option value="">Выберите шаблон</option>
                      {templates.map((t) => (
                        <option key={t.id} value={t.id}>{t.name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Владелец</label>
                    <select name="ownerId" className="w-full p-2 border rounded">
                      <option value="">Без владельца</option>
                      {players.map((p) => (
                        <option key={p.id} value={p.id}>{p.telegramId || p.walletAddress || p.id}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Опыт (XP)</label>
                    <input name="xp" type="number" defaultValue={0} className="w-full p-2 border rounded" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Текущая энергия</label>
                    <input name="energy" type="number" defaultValue={100} className="w-full p-2 border rounded" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Максимальная энергия</label>
                    <input name="maxEnergy" type="number" defaultValue={100} className="w-full p-2 border rounded" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Маневр</label>
                    <input name="maneuver" type="number" placeholder="Авто из шаблона" className="w-full p-2 border rounded" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Импульс</label>
                    <input name="impulse" type="number" placeholder="Авто из шаблона" className="w-full p-2 border rounded" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Текучесть</label>
                    <input name="fluidity" type="number" placeholder="Авто из шаблона" className="w-full p-2 border rounded" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Глубинность</label>
                    <input name="depth" type="number" placeholder="Авто из шаблона" className="w-full p-2 border rounded" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Реакция</label>
                    <input name="reaction" type="number" placeholder="Авто из шаблона" className="w-full p-2 border rounded" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Поток</label>
                    <input name="flow" type="number" placeholder="Авто из шаблона" className="w-full p-2 border rounded" />
                  </div>
                </div>
                <button type="submit" className="mt-4 px-4 py-2 bg-green-500 text-white rounded">
                  Создать
                </button>
              </form>
            )}

            {editingSpirit && (
              <form onSubmit={handleUpdateSpirit} className="mb-6 p-4 bg-white rounded shadow">
                <h2 className="text-xl font-bold mb-4">Редактировать спирит</h2>
                <div className="grid grid-cols-2 gap-4">
                  <input name="level" type="number" placeholder="Уровень" defaultValue={editingSpirit.level} className="p-2 border rounded" />
                  <input name="xp" type="number" placeholder="XP" defaultValue={editingSpirit.xp} className="p-2 border rounded" />
                  <input name="hunger" type="number" placeholder="Голод" defaultValue={editingSpirit.hunger} className="p-2 border rounded" />
                  <input name="energy" type="number" placeholder="Энергия" defaultValue={editingSpirit.energy} className="p-2 border rounded" />
                  <input name="maxEnergy" type="number" placeholder="Макс энергия" defaultValue={editingSpirit.maxEnergy} className="p-2 border rounded" />
                  <input name="maneuver" type="number" placeholder="Маневр" defaultValue={editingSpirit.maneuver} className="p-2 border rounded" />
                  <input name="impulse" type="number" placeholder="Импульс" defaultValue={editingSpirit.impulse} className="p-2 border rounded" />
                  <input name="fluidity" type="number" placeholder="Текучесть" defaultValue={editingSpirit.fluidity} className="p-2 border rounded" />
                  <input name="depth" type="number" placeholder="Глубинность" defaultValue={editingSpirit.depth} className="p-2 border rounded" />
                  <input name="reaction" type="number" placeholder="Реакция" defaultValue={editingSpirit.reaction} className="p-2 border rounded" />
                  <input name="flow" type="number" placeholder="Поток" defaultValue={editingSpirit.flow} className="p-2 border rounded" />
                  <select name="ownerId" defaultValue={editingSpirit.ownerId || ''} className="p-2 border rounded">
                    <option value="">Без владельца</option>
                    {players.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.telegramId || p.walletAddress || p.id}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="flex gap-2 mt-4">
                  <button type="submit" className="px-4 py-2 bg-green-500 text-white rounded">
                    Сохранить
                  </button>
                  <button
                    type="button"
                    onClick={() => setEditingSpirit(null)}
                    className="px-4 py-2 bg-gray-500 text-white rounded"
                  >
                    Отмена
                  </button>
                </div>
              </form>
            )}

            <button
              onClick={() => setShowSpiritFilters(!showSpiritFilters)}
              className="mb-2 px-2 py-1 bg-gray-500 text-white rounded text-xs"
            >
              {showSpiritFilters ? 'Скрыть фильтры' : 'Показать фильтры'}
            </button>

            {showSpiritFilters && (
              <div className="mb-4 p-3 bg-white rounded shadow">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium mb-1">Название</label>
                    <input
                      type="text"
                      placeholder="Фильтр..."
                      value={spiritNameFilter}
                      onChange={(e) => setSpiritNameFilter(e.target.value)}
                      className="w-full p-1 border rounded text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium mb-1">Элемент</label>
                    <select
                      value={spiritElementFilter}
                      onChange={(e) => setSpiritElementFilter(e.target.value)}
                      className="w-full p-1 border rounded text-sm"
                    >
                      <option value="">Все</option>
                      <option value="AIR">AIR</option>
                      <option value="WATER">WATER</option>
                      <option value="EARTH">EARTH</option>
                      <option value="LIGHTNING">LIGHTNING</option>
                      <option value="FOREST">FOREST</option>
                    </select>
                  </div>
                </div>
              </div>
            )}

            <div className="bg-white rounded shadow overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-100 border-b">
                  <tr>
                    <th className="p-3 text-left cursor-pointer hover:bg-gray-200" onClick={() => toggleSpiritSort('name')}>
                      Название {spiritSort === 'name' && (spiritSortDir === 'asc' ? '↑' : '↓')}
                    </th>
                    <th className="p-3 text-left">Элемент</th>
                    <th className="p-3 text-left cursor-pointer hover:bg-gray-200" onClick={() => toggleSpiritSort('level')}>
                      Уровень {spiritSort === 'level' && (spiritSortDir === 'asc' ? '↑' : '↓')}
                    </th>
                    <th className="p-3 text-left">XP</th>
                    <th className="p-3 text-left cursor-pointer hover:bg-gray-200" onClick={() => toggleSpiritSort('energy')}>
                      Энергия {spiritSort === 'energy' && (spiritSortDir === 'asc' ? '↑' : '↓')}
                    </th>
                    <th className="p-3 text-left">Статы</th>
                    <th className="p-3 text-left">Владелец</th>
                    <th className="p-3 text-right">Действия</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredSpirits.map((spirit) => (
                    <tr key={spirit.id} className="border-b hover:bg-gray-50">
                      <td className="p-3 font-medium">{spirit.template.name}</td>
                      <td className="p-3">{spirit.template.element}</td>
                      <td className="p-3">{spirit.level}</td>
                      <td className="p-3">{spirit.xp}</td>
                      <td className="p-3">{spirit.energy}/{spirit.maxEnergy}</td>
                      <td className="p-3 text-xs">
                        М{spirit.maneuver} И{spirit.impulse} Т{spirit.fluidity} Г{spirit.depth} Р{spirit.reaction} П{spirit.flow}
                      </td>
                      <td className="p-3 text-sm">{spirit.owner?.telegramId || '-'}</td>
                      <td className="p-3 text-right">
                        <div className="flex gap-2 justify-end">
                          <button
                            onClick={() => setEditingSpirit(spirit)}
                            className="px-2 py-1 bg-blue-500 text-white rounded text-xs"
                          >
                            Изм
                          </button>
                          <button
                            onClick={() => handleDeleteSpirit(spirit.id)}
                            className="px-2 py-1 bg-red-500 text-white rounded text-xs"
                          >
                            Удал
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'players' && (
          <div>
            <button
              onClick={() => setShowPlayerForm(!showPlayerForm)}
              className="mb-2 px-2 py-1 bg-blue-500 text-white rounded text-xs"
            >
              {showPlayerForm ? 'Отмена' : 'Добавить игрока'}
            </button>

            {showPlayerForm && (
              <form onSubmit={handleCreatePlayer} className="mb-6 p-4 bg-white rounded shadow">
                <h2 className="text-xl font-bold mb-4">Новый игрок</h2>
                <div className="grid grid-cols-2 gap-4">
                  <input name="telegramId" placeholder="Telegram ID (опционально)" className="p-2 border rounded" />
                  <input name="walletAddress" placeholder="Wallet Address (опционально)" className="p-2 border rounded" />
                </div>
                <button type="submit" className="mt-4 px-4 py-2 bg-green-500 text-white rounded">
                  Создать
                </button>
              </form>
            )}

            {editingPlayer && (
              <form onSubmit={handleUpdatePlayer} className="mb-6 p-4 bg-white rounded shadow">
                <h2 className="text-xl font-bold mb-4">Редактировать игрока</h2>
                <div className="grid grid-cols-2 gap-4">
                  <input name="telegramId" placeholder="Telegram ID (опционально)" defaultValue={editingPlayer.telegramId || ''} className="p-2 border rounded" />
                  <input name="walletAddress" placeholder="Wallet Address (опционально)" defaultValue={editingPlayer.walletAddress || ''} className="p-2 border rounded" />
                </div>
                <div className="flex gap-2 mt-4">
                  <button type="submit" className="px-4 py-2 bg-green-500 text-white rounded">
                    Сохранить
                  </button>
                  <button
                    type="button"
                    onClick={() => setEditingPlayer(null)}
                    className="px-4 py-2 bg-gray-500 text-white rounded"
                  >
                    Отмена
                  </button>
                </div>
              </form>
            )}

            {banningPlayer && (
              <div className="mb-6 p-4 bg-white rounded shadow">
                <h2 className="text-xl font-bold mb-4">
                  Забанить игрока: {banningPlayer.telegramId || banningPlayer.walletAddress || banningPlayer.id}
                </h2>
                <div className="mb-4">
                  <input
                    type="text"
                    value={banReason}
                    onChange={(e) => setBanReason(e.target.value)}
                    placeholder="Причина бана (опционально)"
                    className="w-full p-2 border rounded"
                  />
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={handleBanPlayer}
                    className="px-4 py-2 bg-red-500 text-white rounded"
                  >
                    Забанить
                  </button>
                  <button
                    onClick={() => {
                      setBanningPlayer(null)
                      setBanReason('')
                    }}
                    className="px-4 py-2 bg-gray-500 text-white rounded"
                  >
                    Отмена
                  </button>
                </div>
              </div>
            )}

            <div className="space-y-4">
              {players.map((player) => (
                <div
                  key={player.id}
                  className={`p-4 rounded shadow ${player.isBanned ? 'bg-red-50 border-2 border-red-300' : 'bg-white'}`}
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="font-bold">
                        {player.telegramId || player.walletAddress || player.id}
                        {player.isBanned && (
                          <span className="ml-2 px-2 py-1 bg-red-500 text-white text-xs rounded">
                            ЗАБАНЕН
                          </span>
                        )}
                      </h3>
                      <p className="text-sm text-gray-600">ID: {player.id}</p>
                      {player.isBanned && player.banReason && (
                        <p className="text-sm text-red-600 mt-1">Причина: {player.banReason}</p>
                      )}
                      {player.isBanned && player.bannedAt && (
                        <p className="text-xs text-gray-500">
                          Дата бана: {new Date(player.bannedAt).toLocaleString('ru-RU')}
                        </p>
                      )}
                    </div>
                    <div>
                      {player.isBanned ? (
                        <button
                          onClick={() => handleUnbanPlayer(player.id)}
                          className="px-3 py-1 bg-green-500 text-white rounded text-sm"
                        >
                          Разбанить
                        </button>
                      ) : (
                        <button
                          onClick={() => setBanningPlayer(player)}
                          className="px-3 py-1 bg-red-500 text-white rounded text-sm"
                        >
                          Забанить
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div className="bg-white rounded shadow overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-100 border-b">
                  <tr>
                    <th className="p-3 text-left">Telegram ID</th>
                    <th className="p-3 text-left">Кошелёк</th>
                    <th className="p-3 text-right">Действия</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredPlayers.map((player) => (
                    <tr key={player.id} className="border-b hover:bg-gray-50">
                      <td className="p-3">{player.telegramId || '-'}</td>
                      <td className="p-3 font-mono text-xs">{player.walletAddress || '-'}</td>
                      <td className="p-3 text-right">
                        <div className="flex gap-2 justify-end">
                          <button
                            onClick={() => setEditingPlayer(player)}
                            className="px-2 py-1 bg-blue-500 text-white rounded text-xs"
                          >
                            Изм
                          </button>
                          <button
                            onClick={() => handleDeletePlayer(player.id)}
                            className="px-2 py-1 bg-red-500 text-white rounded text-xs"
                          >
                            Удал
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
