import type { LocationInfo } from './api'

function serverUrl(serverId: string): string {
  return `https://discord.com/channels/${serverId}`
}

function channelUrl(serverId: string, channelId: string): string {
  return `https://discord.com/channels/${serverId}/${channelId}`
}

export function DiscordLocation({ server_id, server_name, channel_id, channel_name }: LocationInfo) {
  if (!server_id && !channel_id) {
    return <span className="location location--dm">DM</span>
  }

  return (
    <span className="location">
      {server_id && server_name && (
        <a href={serverUrl(server_id)} target="_blank" rel="noopener noreferrer" className="location__server">
          {server_name}
        </a>
      )}
      {server_id && channel_id && channel_name && (
        <>
          {' / '}
          <a
            href={channelUrl(server_id, channel_id)}
            target="_blank"
            rel="noopener noreferrer"
            className="location__channel"
          >
            #{channel_name}
          </a>
        </>
      )}
      {!server_id && channel_id && channel_name && (
        <span className="location__channel">#{channel_name}</span>
      )}
    </span>
  )
}
