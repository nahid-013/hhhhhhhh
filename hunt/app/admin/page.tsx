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
  perk?: string
}

type Spirit = {
  id: string
  templateId: string
  template: SpiritTemplate
  ownerId?: string
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
  const [editingSpirit, setEditingSpirit] = useState<Spirit | null>(null)
  const [selectedPlayer, setSelectedPlayer] = useState<string>('')
  const [selectedSpirit, setSelectedSpirit] = useState<string>('')
  const [banningPlayer, setBanningPlayer] = useState<Player | null>(null)
  const [banReason, setBanReason] = useState<string>('')

  useEffect(() => {
    loadTemplates()
    loadSpirits()
    loadPlayers()
  }, [])

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
    const formData = new FormData(e.currentTarget)
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
      perk: formData.get('perk') || undefined,
    }

    await fetch('/api/admin/templates', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })

    loadTemplates()
    setShowTemplateForm(false)
    e.currentTarget.reset()
  }

  const handleCreateSpirit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
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

    loadSpirits()
    setShowSpiritForm(false)
    e.currentTarget.reset()
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
    if (formData.get('ownerId')) data.ownerId = formData.get('ownerId') || null

    await fetch(`/api/admin/spirits/${editingSpirit.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })

    loadSpirits()
    setEditingSpirit(null)
  }

  const handleAddSpiritToPlayer = async () => {
    if (!selectedPlayer || !selectedSpirit) return

    await fetch(`/api/admin/players/${selectedPlayer}/spirits`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ spiritId: selectedSpirit }),
    })

    loadPlayers()
    setSelectedPlayer('')
    setSelectedSpirit('')
  }

  const handleCreatePlayer = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    const data = {
      telegramId: formData.get('telegramId') || undefined,
      walletAddress: formData.get('walletAddress') || undefined,
    }

    await fetch('/api/admin/players', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })

    loadPlayers()
    setShowPlayerForm(false)
    e.currentTarget.reset()
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
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Админка HUNT</h1>

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
              className="mb-4 px-4 py-2 bg-blue-500 text-white rounded"
            >
              {showTemplateForm ? 'Отмена' : 'Добавить шаблон'}
            </button>

            {showTemplateForm && (
              <form onSubmit={handleCreateTemplate} className="mb-6 p-4 bg-white rounded shadow">
                <h2 className="text-xl font-bold mb-4">Новый шаблон</h2>
                <div className="grid grid-cols-2 gap-4">
                  <input name="name" placeholder="Название" required className="p-2 border rounded" />
                  <select name="element" required className="p-2 border rounded">
                    <option value="AIR">Воздух</option>
                    <option value="WATER">Вода</option>
                    <option value="EARTH">Земля</option>
                    <option value="LIGHTNING">Молния</option>
                    <option value="FOREST">Лес</option>
                  </select>
                  <select name="rarity" required className="p-2 border rounded">
                    <option value="COMMON">Обычный</option>
                    <option value="RARE">Редкий</option>
                    <option value="EPIC">Эпик</option>
                    <option value="LEGENDARY">Легендарный</option>
                    <option value="MYTHIC">Мифик</option>
                  </select>
                  <input name="generation" type="number" placeholder="Поколение" defaultValue={1} className="p-2 border rounded" />
                  <input name="baseManeuver" type="number" placeholder="Маневр" defaultValue={10} className="p-2 border rounded" />
                  <input name="baseImpulse" type="number" placeholder="Импульс" defaultValue={10} className="p-2 border rounded" />
                  <input name="baseFluidity" type="number" placeholder="Текучесть" defaultValue={10} className="p-2 border rounded" />
                  <input name="baseDepth" type="number" placeholder="Глубинность" defaultValue={10} className="p-2 border rounded" />
                  <input name="baseReaction" type="number" placeholder="Реакция" defaultValue={10} className="p-2 border rounded" />
                  <input name="baseFlow" type="number" placeholder="Поток" defaultValue={10} className="p-2 border rounded" />
                  <input name="perk" placeholder="Перк (опционально)" className="p-2 border rounded" />
                </div>
                <button type="submit" className="mt-4 px-4 py-2 bg-green-500 text-white rounded">
                  Создать
                </button>
              </form>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {templates.map((template) => (
                <div key={template.id} className="p-4 bg-white rounded shadow">
                  <h3 className="font-bold">{template.name}</h3>
                  <p className="text-sm text-gray-600">{template.element} / {template.rarity}</p>
                  <p className="text-sm">Поколение: {template.generation}</p>
                  <p className="text-xs mt-2">
                    Статы: М{template.baseManeuver} И{template.baseImpulse} Т{template.baseFluidity} Г{template.baseDepth} Р{template.baseReaction} П{template.baseFlow}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'spirits' && (
          <div>
            <button
              onClick={() => setShowSpiritForm(!showSpiritForm)}
              className="mb-4 px-4 py-2 bg-blue-500 text-white rounded"
            >
              {showSpiritForm ? 'Отмена' : 'Добавить спирит'}
            </button>

            {showSpiritForm && (
              <form onSubmit={handleCreateSpirit} className="mb-6 p-4 bg-white rounded shadow">
                <h2 className="text-xl font-bold mb-4">Новый спирит</h2>
                <div className="grid grid-cols-2 gap-4">
                  <select name="templateId" required className="p-2 border rounded">
                    <option value="">Выберите шаблон</option>
                    {templates.map((t) => (
                      <option key={t.id} value={t.id}>{t.name}</option>
                    ))}
                  </select>
                  <select name="ownerId" className="p-2 border rounded">
                    <option value="">Без владельца</option>
                    {players.map((p) => (
                      <option key={p.id} value={p.id}>{p.telegramId || p.walletAddress || p.id}</option>
                    ))}
                  </select>
                  <input name="level" type="number" placeholder="Уровень" defaultValue={1} className="p-2 border rounded" />
                  <input name="xp" type="number" placeholder="XP" defaultValue={0} className="p-2 border rounded" />
                  <input name="hunger" type="number" placeholder="Голод" defaultValue={100} className="p-2 border rounded" />
                  <input name="energy" type="number" placeholder="Энергия" defaultValue={100} className="p-2 border rounded" />
                  <input name="maxEnergy" type="number" placeholder="Макс энергия" defaultValue={100} className="p-2 border rounded" />
                  <input name="maneuver" type="number" placeholder="Маневр (опционально)" className="p-2 border rounded" />
                  <input name="impulse" type="number" placeholder="Импульс (опционально)" className="p-2 border rounded" />
                  <input name="fluidity" type="number" placeholder="Текучесть (опционально)" className="p-2 border rounded" />
                  <input name="depth" type="number" placeholder="Глубинность (опционально)" className="p-2 border rounded" />
                  <input name="reaction" type="number" placeholder="Реакция (опционально)" className="p-2 border rounded" />
                  <input name="flow" type="number" placeholder="Поток (опционально)" className="p-2 border rounded" />
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

            <div className="space-y-4">
              {spirits.map((spirit) => (
                <div key={spirit.id} className="p-4 bg-white rounded shadow">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="font-bold">{spirit.template.name}</h3>
                      <p className="text-sm text-gray-600">
                        {spirit.template.element} / {spirit.template.rarity} / Ур. {spirit.level}
                      </p>
                      <p className="text-xs mt-1">
                        XP: {spirit.xp} | Голод: {spirit.hunger} | Энергия: {spirit.energy}/{spirit.maxEnergy}
                      </p>
                      <p className="text-xs">
                        Статы: М{spirit.maneuver} И{spirit.impulse} Т{spirit.fluidity} Г{spirit.depth} Р{spirit.reaction} П{spirit.flow}
                      </p>
                      {spirit.ownerId && <p className="text-xs text-blue-600">Владелец: {spirit.ownerId}</p>}
                    </div>
                    <button
                      onClick={() => setEditingSpirit(spirit)}
                      className="px-3 py-1 bg-blue-500 text-white rounded text-sm"
                    >
                      Редактировать
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'players' && (
          <div>
            <button
              onClick={() => setShowPlayerForm(!showPlayerForm)}
              className="mb-4 px-4 py-2 bg-blue-500 text-white rounded"
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

            <div className="mb-6 p-4 bg-white rounded shadow">
              <h2 className="text-xl font-bold mb-4">Добавить спирит игроку</h2>
              <div className="grid grid-cols-2 gap-4 mb-4">
                <select
                  value={selectedPlayer}
                  onChange={(e) => setSelectedPlayer(e.target.value)}
                  className="p-2 border rounded"
                >
                  <option value="">Выберите игрока</option>
                  {players.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.telegramId || p.walletAddress || p.id}
                    </option>
                  ))}
                </select>
                <select
                  value={selectedSpirit}
                  onChange={(e) => setSelectedSpirit(e.target.value)}
                  className="p-2 border rounded"
                >
                  <option value="">Выберите спирит</option>
                  {spirits.filter(s => !s.ownerId).map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.template.name} (Ур. {s.level})
                    </option>
                  ))}
                </select>
              </div>
              <button
                onClick={handleAddSpiritToPlayer}
                disabled={!selectedPlayer || !selectedSpirit}
                className="px-4 py-2 bg-green-500 text-white rounded disabled:bg-gray-300"
              >
                Добавить
              </button>
            </div>

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
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
