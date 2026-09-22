export type PanelMessage = {
  id: number
  direction?: string
  msg_type?: string
  to_wa_id?: string
  template_name?: string
  caption?: string
  local_file_path?: string
  media_id?: string
  meta_message_id?: string
  status?: string
  error_code?: string | number
  error_message?: string
  sistema_origem?: string
  usuario_geph?: string
  hostname?: string
  created_at?: string
  updated_at?: string
}

export type PanelSession = {
  usuario_geph: string
  installation_id: string
  status: string
  connected: boolean
  display_phone?: string | null
  waba_id?: string | null
  last_error?: string | null
}

export type MessagesResponse = {
  usuario_geph: string
  messages: PanelMessage[]
}
