function! EditSnactorResource(type)
        let wordUnderCursor = expand("<cword>")
        let file = system('snactor discover --json | jq -r ".' . a:type . '.' . wordUnderCursor . '.path // \"\""')
        if strlen(file) > 1
            exe 'vsplit ' . file
        else
            echom type . ': ' . wordUnderCursor . ' not found'
        endif
endfunction

nnoremap <silent> <leader>em :call EditSnactorResource('models')<cr>
