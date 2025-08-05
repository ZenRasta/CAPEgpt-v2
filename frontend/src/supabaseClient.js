import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://ocdjqofrcrobgrjyjqox.supabase.co'
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9jZGpxb2ZyY3JvYmdyanlqcW94Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzM5NzIwMjksImV4cCI6MjA0OTU0ODAyOX0.dBmHdnT6BbYJPnOL4y3QrVfCKKyQPKxE5FhOCEX7MaA'

export const supabase = createClient(supabaseUrl, supabaseAnonKey)