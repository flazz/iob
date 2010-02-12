#!/bin/env ruby
require 'nokogiri'
require 'open-uri'

class InOutBoard

  URL = "http://calvin/clockwork/index.php"

  def initialize url=URL
    @url = URI.parse url
  end

  def sign state, message=nil
    doc = Nokogiri::HTML open("#{@url}?go=1")

    form = doc.css("form[name='mainForm']")
    action = form.first['action']

    query = form.css("input", "select", "textarea").inject({}) do |acc, tag|

      case tag.name
      when 'input' then acc.merge tag['name'] => tag['value']
      when 'select' then acc.merge tag['name'] => tag.css("option").first['value']
      when 'textarea' then acc.merge tag['name'] => tag.content
      else acc
      end

    end

    query['in_out'] = case state
                      when :in
                        form.css("select[name = 'in_out'] option:contains('In')").first['value']
                      when :out
                        form.css("select[name = 'in_out'] option:contains('Out')").first['value']
                      end

    query['comment'] = message

    puts query.inspect


    res = Net::HTTP.post_form @url.merge(action), query
    res.error! unless Net::HTTPSuccess === res
  end

  def list
    doc = Nokogiri::HTML open("#{@url}")

    doc.css("tr").map do |row|
      cols = row.css("td")

      if cols.size == 7
        {
          :status => cols[1].content,
          :name => cols[2].content,
          :ext => cols[3].content,
          :email => cols[4].css("a").first['href'].sub(/^mailto:/, ''),
          :time_back => cols[5].content,
          :message => cols[6].content
        }
      end

    end.compact

  end

end

if $0 == __FILE__
  board = InOutBoard.new
  command = ARGV.shift or raise "#{$0} usage: i[n] | o[ut] | l[ist]"
  message = ARGV.shift

  case command
  when /i(n)?/i then board.sign :in, message
  when /o(ut)?/i then board.sign :out, message
  when /l(ist)?/i 

    board.list.each do |p|
      puts p.values_at(:name, :email, :status, :message).join("\t")
    end

  else raise "#{$0} usage: i[n] | o[ut] | l[ist]"
  end

  message = ARGV.shift
end
